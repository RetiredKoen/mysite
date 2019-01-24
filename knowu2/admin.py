from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from .models import Match, Competitor, Question, Answer, Round


class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
        errors = 'ignore'


class AnswerResource(resources.ModelResource):
    question = fields.Field(
        column_name='question',
        attribute='question',
        widget=ForeignKeyWidget(Question, 'question')
    )

    class Meta:
        model = Answer
        errors = 'ignore'


class CompetitorInline(admin.TabularInline):
    model = Competitor
    extra = 4


class RoundInline(admin.TabularInline):
    model = Round
    extra = 2


class MatchAdmin(admin.ModelAdmin):
    inlines = [CompetitorInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '64'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    extra = 2


class QuestionAdmin(ImportExportModelAdmin):
    resource_class = QuestionResource
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '112'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    list_filter = ['category', 'group']
    search_fields = ['question']
    inlines = [AnswerInline]


class AnswerAdmin(ImportExportModelAdmin):
    resource_class = AnswerResource


admin.site.register(Match, MatchAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
