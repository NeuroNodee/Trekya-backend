from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


class NotificationAdminForm(forms.ModelForm):

    
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('Users', is_stacked=False)
    )

    class Meta:
        model = Notification
        fields = ['users', 'status', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            self.fields['users'].initial = self.instance.users.all()

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get('users')

       
        if not users:
            raise forms.ValidationError("Select users.")

        return cleaned_data




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm
    list_display = ('display_users', 'status', 'message', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('message',)

    def display_users(self, obj):
        return ", ".join([user.email for user in obj.users.all()]) or "-"
    display_users.short_description = "Users"