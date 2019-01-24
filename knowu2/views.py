from datetime import timedelta
from random import randint

from django import forms
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone

from knowu2.models import Question, Answer, Match, Competitor, Round, Reply, Quess
from .forms import RoundReplyForm, RoundJudgeForm


def index(request):
    num_questions = Question.objects.all().count()
    num_answers = Answer.objects.all().count()
    num_matches = Match.objects.count()
    num_competitors = Competitor.objects.count()

    cur_match = None
    if request.user.is_authenticated:
        if Match.objects.filter(host=request.user).exists():
            cur_match = Match.objects.get(host=request.user)
            cur_match.last_activity = timezone.localtime()
            cur_match.save()
        elif Competitor.objects.filter(user=request.user).exists():
            cur_competitor = Competitor.objects.get(user=request.user)
            cur_match = cur_competitor.match
            cur_competitor.last_activity = timezone.localtime()
            cur_competitor.save()
            return redirect('round_reply')

    cur_competitors = None
    cur_round = None
    cur_question = None
    cur_answers = None
    cur_replies = None

    if cur_match:
        cur_competitors = Competitor.objects.filter(match=cur_match)
        if Round.objects.filter(match=cur_match, round=cur_match.lap).exists():
            cur_round = Round.objects.get(match=cur_match, round=cur_match.lap)

    if cur_round:
        cur_question = Question.objects.get(round=cur_round)
        cur_answers = Answer.objects.filter(question=cur_question)
        cur_replies = Reply.objects.filter(round=cur_round).all()

    context = {
        'num_questions': num_questions,
        'num_answers': num_answers,
        'num_matches': num_matches,
        'num_competitors': num_competitors,
        'cur_match': cur_match,
        'cur_competitors': cur_competitors,
        'cur_round': cur_round,
        'cur_question': cur_question,
        'cur_answers': cur_answers,
        'cur_replies': cur_replies
    }

    return render(request, 'knowu2/index.html', context)


def game_next_status(request):
    if request.user.is_authenticated and Match.objects.filter(host=request.user).exists():
        cur_match = Match.objects.get(host=request.user)
        if cur_match.status.upper() == 'JOINING':
            cur_match.status = 'RUNNING'
            Round.objects.filter(match=cur_match).delete()
            for lp_competitor in cur_match.competitor_set.all():
                lp_competitor.last_activity = timezone.localtime() - timedelta(minutes=1)
                lp_competitor.correct_times = 0
                lp_competitor.correct_points = 0
                lp_competitor.cmp_cc_times = 0
                lp_competitor.cmp_cw_times = 0
                lp_competitor.cmp_wc_times = 0
                lp_competitor.cmp_ww_times = 0
                lp_competitor.cmp_cc_points = 0
                lp_competitor.cmp_cw_points = 0
                lp_competitor.cmp_wc_points = 0
                lp_competitor.cmp_ww_points = 0
                lp_competitor.rvl_cc_times = 0
                lp_competitor.rvl_cw_times = 0
                lp_competitor.rvl_wc_times = 0
                lp_competitor.rvl_ww_times = 0
                lp_competitor.rvl_cc_points = 0
                lp_competitor.rvl_cw_points = 0
                lp_competitor.rvl_wc_points = 0
                lp_competitor.rvl_ww_points = 0
                lp_competitor.save()
        elif cur_match.status.upper() == 'RUNNING':
            cur_match.status = 'CLOSED'
        elif cur_match.status.upper() == 'CLOSED':
            cur_match.status = 'JOINING'
        cur_match.last_activity = timezone.localtime()
        cur_match.save()
        if cur_match.status.upper() == 'RUNNING':
            return redirect('round_next')

    return redirect('index')


@login_required(login_url='/accounts/login')
def round_reply(request):
    cur_match = None
    cur_round = None

    form_fields = {}
    form_data = {}

    if Competitor.objects.filter(user=request.user).exists():
        cur_competitor = Competitor.objects.get(user=request.user)
        cur_match = cur_competitor.match
        cur_competitor.last_activity = timezone.localtime()
        cur_competitor.save()
    else:
        return redirect('index')
    if Match.objects.filter(host=request.user).exists():
        cur_match = Match.objects.get(host=request.user)
        cur_match.last_activity = timezone.localtime()
        cur_match.save()
    if not cur_match:
        raise Http404("View round_reply no match found, contact developer")

    if Round.objects.filter(match=cur_match, round=cur_match.lap).exists():
        cur_round = Round.objects.get(match=cur_match, round=cur_match.lap)
        cur_question = Question.objects.get(round=cur_round)
        cur_answers = Answer.objects.filter(question=cur_question)
    if not cur_round:
        raise Http404("View round_reply no round found, contact developer")

    question = '{0} - {1} - {2} - {3}'.format(cur_round.round, cur_question.group, cur_question.category, cur_question.question)
    if cur_answers.count() < 2:
        form_data['reply'] = ' '
        form_fields['reply'] = forms.CharField(max_length=64, label='', required=False)
    else:
        wrk_answers = {}
        for answer in cur_answers:
            wrk_answers[answer.answer] = answer.answer
        form_fields['reply'] = forms.ChoiceField(label='', choices=(wrk_answers.items()), widget=forms.RadioSelect(),
                                                 required=False)

    me = None
    rivals = []
    for lp_competitor in cur_match.competitor_set.all():
        cmp_data = dict()
        cmp_data['name'] = lp_competitor.user.username
        cmp_data['status'] = lp_competitor.reply_set.get(round=cur_round).status
        cmp_data['scores'] = '{0} ({1} {2})'.format(lp_competitor.correct_points, lp_competitor.correct_points_rvl,
                                                    lp_competitor.correct_points_cmp)

        if lp_competitor.user == request.user:
            me = cmp_data
        else:
            rivals.append(cmp_data)
            form_fields[lp_competitor.user.username + '_correct'] = forms.IntegerField(min_value=0, max_value=10,
                                                                                       label='', required=False)
            form_fields[lp_competitor.user.username + '_wrong'] = forms.IntegerField(min_value=0, max_value=10,
                                                                                     label='', required=False)

    if request.method == 'POST':
        dyn_round_reply_form = type('DynRoundReplyForm', (RoundReplyForm,), form_fields)
        form = dyn_round_reply_form(request.POST)
        if form.is_valid():
            cur_reply = Reply.objects.get(round=cur_round, competitor=cur_competitor)
            cur_reply.reply = form.cleaned_data['reply']
            cur_reply.status = 'REPLIED'
            cur_reply.save()
            for lp_quess in cur_reply.quess_set.all():
                rival = lp_quess.competitor.user.username
                if form.cleaned_data[rival + '_correct'] is not None:
                    lp_quess.points = form.cleaned_data[rival + '_correct']
                    lp_quess.quess = 'CORRECT'
                elif form.cleaned_data[rival + '_wrong'] is not None:
                    lp_quess.points = form.cleaned_data[rival + '_wrong']
                    lp_quess.quess = 'WRONG'
                else:
                    lp_quess.quess = 'PASS'
                lp_quess.save()
                new_round_status = 'REPLIED'
            for cur_reply in cur_round.reply_set.all():
                if cur_reply.status != 'REPLIED':
                    new_round_status = 'PENDING'
                    break
            cur_round.status = new_round_status
            cur_round.save()
            return redirect('index')
    else:
        dyn_round_reply_form = type('DynRoundReplyForm', (RoundReplyForm,), form_fields)
        form = dyn_round_reply_form(form_data)

    context = {
        'cur_match': cur_match,
        'form': form,
        'question': question,
        'me': me,
        'rivals': rivals,
    }

    return render(request, 'knowu2/round_reply.html', context)


@login_required(login_url='/accounts/login')
def round_judge(request):
    cur_match = None
    cur_round = None

    form_fields = {}
    form_data = {}

    if Competitor.objects.filter(user=request.user).exists():
        cur_competitor = Competitor.objects.get(user=request.user)
        cur_match = cur_competitor.match
    if Match.objects.filter(host=request.user).exists():
        cur_match = Match.objects.get(host=request.user)
    else:
        return redirect('round_judge')
    if not cur_match:
        raise Http404("View round_judge no match found, contact developer")

    if Round.objects.filter(match=cur_match, round=cur_match.lap).exists():
        cur_round = Round.objects.get(match=cur_match, round=cur_match.lap)
        cur_question = Question.objects.get(round=cur_round)
        cur_answers = Answer.objects.filter(question=cur_question)
    if not cur_round:
        raise Http404("View round_judge no round found, contact developer")

    question = cur_question.question
    for answer in cur_answers:
        if answer.correct:
            cor_answer = answer.answer
    competitors = []
    for lp_competitor in cur_match.competitor_set.all():
        competitor = lp_competitor.user.username
        competitors.append(competitor)
        cur_reply = Reply.objects.get(round=cur_round, competitor=lp_competitor)
        if cur_reply.reply == cor_answer:
            form_data[competitor + '_correct'] = True
        form_fields[competitor + '_correct'] = forms.BooleanField(label=competitor + ': ' + cur_reply.reply,
                                                                  required=False)

    if request.method == 'POST':
        dyn_round_judge_form = type('DynRoundJudgeForm', (RoundJudgeForm,), form_fields)
        form = dyn_round_judge_form(request.POST)
        if form.is_valid():

            for cmp_reply in cur_round.reply_set.all():
                cur_reply.correct = False
                cur_reply.correct_points = 0
                cmp_reply.cmp_cc_times = 0
                cmp_reply.cmp_cw_times = 0
                cmp_reply.cmp_wc_times = 0
                cmp_reply.cmp_ww_times = 0
                cmp_reply.cmp_cc_points = 0
                cmp_reply.cmp_cw_points = 0
                cmp_reply.cmp_wc_points = 0
                cmp_reply.cmp_ww_points = 0
                cmp_reply.rvl_cc_times = 0
                cmp_reply.rvl_cw_times = 0
                cmp_reply.rvl_wc_times = 0
                cmp_reply.rvl_ww_times = 0
                cmp_reply.rvl_cc_points = 0
                cmp_reply.rvl_cw_points = 0
                cmp_reply.rvl_wc_points = 0
                cmp_reply.rvl_ww_points = 0
                cmp_reply.save()

            for lp_competitor in cur_match.competitor_set.all():
                competitor = lp_competitor.user.username
                cur_reply = Reply.objects.get(round=cur_round, competitor=lp_competitor)
                cur_reply.correct = form.cleaned_data[competitor + '_correct']
                if cur_reply.correct:
                    cur_reply.correct_points = 20 * (cur_match.competitor_set.count() - 1)
                else:
                    cur_reply.correct_points = 0
                cur_reply.status = 'JUDGED'
                cur_reply.save()
            cur_round.status = 'JUDGED'
            cur_round.save()

            for cmp_reply in cur_round.reply_set.all():
                for rvl_reply in cur_round.reply_set.all():
                    if cmp_reply != rvl_reply:
                        for lp_quess in rvl_reply.quess_set.all():
                            if lp_quess.competitor == cmp_reply.competitor:
                                if cmp_reply.correct:
                                    if lp_quess.quess == 'CORRECT':
                                        rvl_reply.rvl_cc_times += 1
                                        rvl_reply.rvl_cc_points += lp_quess.points
                                    elif lp_quess.quess == 'WRONG':
                                        rvl_reply.rvl_cw_times += 1
                                        rvl_reply.rvl_cw_points -= lp_quess.points
                                else:
                                    if lp_quess.quess == 'CORRECT':
                                        rvl_reply.rvl_wc_times += 1
                                        rvl_reply.rvl_wc_points -= lp_quess.points
                                    elif lp_quess.quess == 'WRONG':
                                        rvl_reply.rvl_ww_times += 1
                                        rvl_reply.rvl_ww_points += lp_quess.points
                                rvl_reply.save()

            for cmp_reply in cur_round.reply_set.all():
                for rvl_reply in cur_round.reply_set.all():
                    if cmp_reply != rvl_reply:
                        for lp_quess in rvl_reply.quess_set.all():
                            if lp_quess.competitor == cmp_reply.competitor:
                                if cmp_reply.correct:
                                    if lp_quess.quess == 'CORRECT':
                                        cmp_reply.cmp_cc_times += 1
                                        cmp_reply.cmp_cc_points -= lp_quess.points
                                    elif lp_quess.quess == 'WRONG':
                                        cmp_reply.cmp_cw_times += 1
                                        cmp_reply.cmp_cw_points += lp_quess.points
                                else:
                                    if lp_quess.quess == 'CORRECT':
                                        cmp_reply.cmp_wc_times += 1
                                        cmp_reply.cmp_wc_points -= lp_quess.points
                                    elif lp_quess.quess == 'WRONG':
                                        cmp_reply.cmp_ww_times += 1
                                        cmp_reply.cmp_ww_points += lp_quess.points
                                cmp_reply.save()
        return redirect('index')
    else:
        dyn_round_judge_form = type('DynRoundJudgeForm', (RoundJudgeForm,), form_fields)
        form = dyn_round_judge_form(form_data)

    context = {
        'cur_match': cur_match,
        'form': form,
        'question': question,
        'answer': cor_answer,
        'competitors': competitors,
    }

    return render(request, 'knowu2/round_judge.html', context)


@login_required(login_url='/accounts/login')
def round_result(request):
    cur_match = None
    cur_round = None

    if Competitor.objects.filter(user=request.user).exists():
        cur_competitor = Competitor.objects.get(user=request.user)
        cur_match = cur_competitor.match
    if Match.objects.filter(host=request.user).exists():
        cur_match = Match.objects.get(host=request.user)
    if not cur_match:
        raise Http404("View round_result no match found, contact developer")

    if Round.objects.filter(match=cur_match, round=cur_match.lap).exists():
        cur_round = Round.objects.get(match=cur_match, round=cur_match.lap)
        cur_question = Question.objects.get(round=cur_round)
        cur_answers = Answer.objects.filter(question=cur_question)
    if not cur_round:
        raise Http404("View round_result no round found, contact developer")

    question = cur_question.question
    for answer in cur_answers:
        if answer.correct:
            answer = answer.answer

    competitors = []
    for lp_competitor in cur_match.competitor_set.all():
        competitor = lp_competitor.user.username
        competitors.append(competitor)

    reply_points = 20 * (cur_match.competitor_set.count() - 1)
    lines = []

    # for cmp_reply in cur_round.reply_set.all():
    #     line = dict()
    #     line['type'] = 'rvl-det'
    #     line['key1'] = cmp_reply.competitor.user.username
    #     line['key2'] = 'debugger'
    #     line['text1'] = 'rvl: cc: {0} {1} cw: {2} {3} wc: {4} {5} ww: {6} {7} '.format(cmp_reply.rvl_cc_times,
    #                                                                                    cmp_reply.rvl_cc_points,
    #                                                                                    cmp_reply.rvl_cw_times,
    #                                                                                    cmp_reply.rvl_cw_points,
    #                                                                                    cmp_reply.rvl_wc_times,
    #                                                                                    cmp_reply.rvl_wc_points,
    #                                                                                    cmp_reply.rvl_ww_times,
    #                                                                                    cmp_reply.rvl_ww_points)
    #     line['correct'] = True
    #     line['points'] = 0
    #     lines.append(line)
    #     line = dict()
    #     line['type'] = 'cmp-det'
    #     line['key1'] = cmp_reply.competitor.user.username
    #     line['key2'] = 'debugger'
    #     line['text1'] = 'cmp: cc: {0} {1} cw: {2} {3} wc: {4} {5} ww: {6} {7} '.format(cmp_reply.cmp_cc_times,
    #                                                                                    cmp_reply.cmp_cc_points,
    #                                                                                    cmp_reply.cmp_cw_times,
    #                                                                                    cmp_reply.cmp_cw_points,
    #                                                                                    cmp_reply.cmp_wc_times,
    #                                                                                    cmp_reply.cmp_wc_points,
    #                                                                                    cmp_reply.cmp_ww_times,
    #                                                                                    cmp_reply.cmp_ww_points)
    #     line['correct'] = True
    #     line['points'] = 0
    #     lines.append(line)
    #
    for cmp_reply in cur_round.reply_set.all():
        line = dict()
        line['type'] = 'cmp-head'
        line['key1'] = cmp_reply.competitor.user.username
        line['key2'] = None
        line['text1'] = cmp_reply.reply
        line['correct'] = cmp_reply.correct
        if cmp_reply.correct:
            line['points'] = reply_points
        else:
            line['points'] = 0
        lines.append(line)
        for rvl_reply in cur_round.reply_set.all():
            if cmp_reply != rvl_reply:
                for lp_quess in rvl_reply.quess_set.all():
                    if lp_quess.competitor == cmp_reply.competitor:
                        if cmp_reply.correct:
                            if lp_quess.quess == 'CORRECT':
                                line = dict()
                                line['type'] = 'rvl-det'
                                line['key1'] = rvl_reply.competitor.user.username
                                line['key2'] = cmp_reply.competitor.user.username
                                line['text1'] = '{0} expected {1} to be correct'.format(line['key1'], line['key2'])
                                line['correct'] = True
                                line['points'] = lp_quess.points
                                lines.append(line)
                                line = dict()
                                line['type'] = 'cmp-det'
                                line['key1'] = cmp_reply.competitor.user.username
                                line['key2'] = rvl_reply.competitor.user.username
                                line['text1'] = 'expected {0} to be correct'.format(line['key1'])
                                line['correct'] = True
                                line['points'] = lp_quess.points * -1
                                lines.append(line)
                            elif lp_quess.quess == 'WRONG':
                                line = dict()
                                line['type'] = 'rvl-det'
                                line['key1'] = rvl_reply.competitor.user.username
                                line['key2'] = cmp_reply.competitor.user.username
                                line['text1'] = '{0} expected {1} to be wrong'.format(line['key1'], line['key2'])
                                line['correct'] = False
                                line['points'] = lp_quess.points * -1
                                lines.append(line)
                                line = dict()
                                line['type'] = 'cmp-det'
                                line['key1'] = cmp_reply.competitor.user.username
                                line['key2'] = rvl_reply.competitor.user.username
                                line['text1'] = 'expected {0} to be wrong'.format(line['key1'])
                                line['correct'] = False
                                line['points'] = lp_quess.points
                                lines.append(line)
                        else:
                            if lp_quess.quess == 'CORRECT':
                                line = dict()
                                line['type'] = 'rvl-det'
                                line['key1'] = rvl_reply.competitor.user.username
                                line['key2'] = cmp_reply.competitor.user.username
                                line['text1'] = '{0} expected {1} to be correct'.format(line['key1'], line['key2'])
                                line['correct'] = False
                                line['points'] = lp_quess.points * -1
                                lines.append(line)
                                line = dict()
                                line['type'] = 'cmp-det'
                                line['key1'] = cmp_reply.competitor.user.username
                                line['key2'] = rvl_reply.competitor.user.username
                                line['text1'] = 'expected {0} to be correct'.format(line['key1'])
                                line['correct'] = False
                                line['points'] = lp_quess.points * -1
                                lines.append(line)
                            elif lp_quess.quess == 'WRONG':
                                line = dict()
                                line['type'] = 'rvl-det'
                                line['key1'] = rvl_reply.competitor.user.username
                                line['key2'] = cmp_reply.competitor.user.username
                                line['text1'] = '{0} expected {1} to be wrong'.format(line['key1'], line['key2'])
                                line['correct'] = True
                                line['points'] = lp_quess.points
                                lines.append(line)
                                line = dict()
                                line['type'] = 'cmp-det'
                                line['key1'] = cmp_reply.competitor.user.username
                                line['key2'] = rvl_reply.competitor.user.username
                                line['text1'] = 'expected {0} to be wrong'.format(line['key1'])
                                line['correct'] = True
                                line['points'] = lp_quess.points
                                lines.append(line)
    for lp_competitor in competitors:
        total_head = 0
        nmb_betting_on = 0
        nmb_betting_by = 0
        total_betting_on = 0
        total_betting_by = 0
        for line in lines:
            if line['key1'] == lp_competitor:
                if line['type'] == 'cmp-head':
                    total_head += line['points']
                if line['type'] == 'rvl-det' and line['key1'] != 'debugger':
                    nmb_betting_on += 1
                    total_betting_on += line['points']
                if line['type'] == 'cmp-det' and line['key1'] != 'debugger':
                    nmb_betting_by += 1
                    total_betting_by += line['points']
        if nmb_betting_on > 0:
            line = dict()
            line['type'] = 'rvl-tot'
            line['key1'] = lp_competitor
            line['key2'] = None
            line['text1'] = 'Including betting ON rivals'
            line['correct'] = False
            line['points'] = total_head + total_betting_on
            lines.append(line)
        if nmb_betting_by > 0:
            line = dict()
            line['type'] = 'cmp-tot'
            line['key1'] = lp_competitor
            line['key2'] = None
            line['text1'] = 'Including betting BY rivals'
            line['correct'] = False
            line['points'] = total_head + total_betting_on + total_betting_by
            lines.append(line)

    context = {
        'cur_match': cur_match,
        'question': question,
        'answer': answer,
        'competitors': competitors,
        'lines': lines
    }

    return render(request, 'knowu2/round_result.html', context)


def round_next(request):
    if request.user.is_authenticated and Match.objects.filter(host=request.user).exists():
        cur_match = Match.objects.get(host=request.user)
    else:
        raise Http404("View round_next no match found, contact developer")

    old_round = None
    if Round.objects.filter(match=cur_match, round=cur_match.lap).exists():
        old_round = Round.objects.get(match=cur_match, round=cur_match.lap)
        old_round.status = 'FINISHED'
        old_round.save()
        for lp_competitor in cur_match.competitor_set.all():
            for lp_reply in lp_competitor.reply_set.filter(round=old_round):
                if lp_reply.correct:
                    lp_competitor.correct_times += 1
                lp_competitor.correct_points += lp_reply.correct_points
                lp_competitor.cmp_cc_times += lp_reply.cmp_cc_times
                lp_competitor.cmp_cw_times += lp_reply.cmp_cw_times
                lp_competitor.cmp_wc_times += lp_reply.cmp_wc_times
                lp_competitor.cmp_ww_times += lp_reply.cmp_ww_times
                lp_competitor.cmp_cc_points += lp_reply.cmp_cc_points
                lp_competitor.cmp_cw_points += lp_reply.cmp_cw_points
                lp_competitor.cmp_wc_points += lp_reply.cmp_wc_points
                lp_competitor.cmp_ww_points += lp_reply.cmp_ww_points
                lp_competitor.rvl_cc_times += lp_reply.rvl_cc_times
                lp_competitor.rvl_cw_times += lp_reply.rvl_cw_times
                lp_competitor.rvl_wc_times += lp_reply.rvl_wc_times
                lp_competitor.rvl_ww_times += lp_reply.rvl_ww_times
                lp_competitor.rvl_cc_points += lp_reply.rvl_cc_points
                lp_competitor.rvl_cw_points += lp_reply.rvl_cw_points
                lp_competitor.rvl_wc_points += lp_reply.rvl_wc_points
                lp_competitor.rvl_ww_points += lp_reply.rvl_ww_points
                lp_competitor.save()

    num_questions = Question.objects.all().count()
    while True:
        new_question_pk = randint(0, num_questions - 1) * 10
        if Question.objects.filter(pk=new_question_pk).exists():
            if not Question.objects.filter(pk=new_question_pk, round__match=cur_match).exists():
                break
    new_question = Question.objects.get(pk=new_question_pk)

    if old_round:
        new_round = Round(match=cur_match, question=new_question, round=old_round.round + 1, status='PENDING')
    else:
        new_round = Round(match=cur_match, question=new_question, round=1, status='PENDING')
    new_round.save()
    cur_match.lap = new_round.round
    cur_match.save()

    for rpl_competitor in cur_match.competitor_set.all():
        new_reply = Reply(competitor=rpl_competitor, round=new_round, status='PENDING')
        new_reply.save()
        for qss_competitor in cur_match.competitor_set.all():
            if rpl_competitor != qss_competitor:
                new_quess = Quess(competitor=qss_competitor, reply=new_reply, quess='PASS')
                new_quess.save()

    return redirect('index')
