# PR2018-04-27
from import_export import resources
from .models import Schooldefault

class SchoolcodeResource(resources.ModelResource):

    class Meta:
        model = Schooldefault