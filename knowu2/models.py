from django.contrib.auth.models import User
from django.db import models


class Question(models.Model):
    category = models.CharField(max_length=24)
    group = models.CharField(max_length=24)
    question = models.CharField(max_length=128)

    def __str__(self):
        return self.question


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, )
    answer = models.CharField(max_length=64)
    correct = models.BooleanField()

    def __str__(self):
        return self.answer


class Match(models.Model):
    STATUSES = (
        ('JOINING', 'Joining'),
        ('RUNNING', 'Running'),
        ('CLOSED', 'Closed'),
    )
    host = models.ForeignKey(User, on_delete=models.CASCADE, )
    match = models.CharField(max_length=32)
    lap = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUSES)
    testing = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'matches'

    def __str__(self):
        return self.match


class Competitor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, )
    match = models.ForeignKey(Match, on_delete=models.CASCADE, )
    last_activity = models.DateTimeField(null=True, blank=True)
    correct_times = models.IntegerField(default=0)
    correct_points = models.IntegerField(default=0)
    cmp_cc_times = models.IntegerField(default=0)
    cmp_cw_times = models.IntegerField(default=0)
    cmp_wc_times = models.IntegerField(default=0)
    cmp_ww_times = models.IntegerField(default=0)
    cmp_cc_points = models.IntegerField(default=0)
    cmp_cw_points = models.IntegerField(default=0)
    cmp_wc_points = models.IntegerField(default=0)
    cmp_ww_points = models.IntegerField(default=0)
    rvl_cc_times = models.IntegerField(default=0)
    rvl_cw_times = models.IntegerField(default=0)
    rvl_wc_times = models.IntegerField(default=0)
    rvl_ww_times = models.IntegerField(default=0)
    rvl_cc_points = models.IntegerField(default=0)
    rvl_cw_points = models.IntegerField(default=0)
    rvl_wc_points = models.IntegerField(default=0)
    rvl_ww_points = models.IntegerField(default=0)

    def __str__(self):
        return self.user.last_name + ', ' + self.user.first_name

    @property
    def correct_points_rvl(self):
        correct_points_rvl = self.correct_points +  self.rvl_cc_points + self.rvl_cw_points + self.rvl_wc_points + self.rvl_ww_points
        return correct_points_rvl

    @property
    def correct_points_cmp(self):
        correct_points_cmp = self.correct_points_rvl +  self.cmp_cc_points + self.cmp_cw_points + self.cmp_wc_points + self.cmp_ww_points
        return correct_points_cmp


class Round(models.Model):
    STATUSES = (
        ('PENDING', 'Pending'),
        ('REPLIED', 'Replied'),
        ('JUDGED', 'Judged'),
        ('FINISHED', 'Finished'),
    )
    match = models.ForeignKey(Match, on_delete=models.CASCADE, )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, )
    round = models.IntegerField(default=0)
    status = models.CharField(max_length=8, choices=STATUSES)

    def __str__(self):
        return self.status


class Reply(models.Model):
    STATUSES = (
        ('PENDING', 'Pending'),
        ('REPLIED', 'Replied'),
    )
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, )
    round = models.ForeignKey(Round, on_delete=models.CASCADE, )
    reply = models.CharField(max_length=64)
    correct = models.BooleanField(default=False)
    correct_points = models.IntegerField(default=0)
    cmp_cc_times = models.IntegerField(default=0)
    cmp_cw_times = models.IntegerField(default=0)
    cmp_wc_times = models.IntegerField(default=0)
    cmp_ww_times = models.IntegerField(default=0)
    cmp_cc_points = models.IntegerField(default=0)
    cmp_cw_points = models.IntegerField(default=0)
    cmp_wc_points = models.IntegerField(default=0)
    cmp_ww_points = models.IntegerField(default=0)
    rvl_cc_times = models.IntegerField(default=0)
    rvl_cw_times = models.IntegerField(default=0)
    rvl_wc_times = models.IntegerField(default=0)
    rvl_ww_times = models.IntegerField(default=0)
    rvl_cc_points = models.IntegerField(default=0)
    rvl_cw_points = models.IntegerField(default=0)
    rvl_wc_points = models.IntegerField(default=0)
    rvl_ww_points = models.IntegerField(default=0)
    status = models.CharField(max_length=8, choices=STATUSES)

    def __str__(self):
        return self.reply

    @property
    def correct_points_rvl(self):
        correct_points_rvl = self.correct_points +  self.rvl_cc_points + self.rvl_cw_points + self.rvl_wc_points + self.rvl_ww_points
        return correct_points_rvl

    @property
    def correct_points_cmp(self):
        correct_points_cmp = self.correct_points_rvl +  self.cmp_cc_points + self.cmp_cw_points + self.cmp_wc_points + self.cmp_ww_points
        return correct_points_cmp


class Quess(models.Model):
    QUESSES = (
        ('PASS', 'Pass'),
        ('CORRECT', 'Correct'),
        ('WRONG', 'Wrong'),
    )
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, )
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, )
    quess = models.CharField(max_length=8, choices=QUESSES)
    points = models.IntegerField(default=0)
    correct = models.BooleanField(default=False)
