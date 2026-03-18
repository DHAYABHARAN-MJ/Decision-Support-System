# dss/urls.py
from django.urls import path
from .views import (
    AssessView,
    ScoreOnlyView,
    FlagsOnlyView,
    ParameterRulesView,
    CompoundRulesView,
)

urlpatterns = [
    path("assess/",         AssessView.as_view(),         name="dss-assess"),
    path("score/",          ScoreOnlyView.as_view(),       name="dss-score"),
    path("flags/",          FlagsOnlyView.as_view(),       name="dss-flags"),
    path("rules/",          ParameterRulesView.as_view(),  name="dss-rules"),
    path("compound-rules/", CompoundRulesView.as_view(),   name="dss-compound-rules"),
]
