from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import SpyCats
from .serializers import SpyCatsSerializer


@admin.register(SpyCats)
class SpyCatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'breed', 'salary')
    search_fields = ('name', 'breed')
    list_filter = ('breed',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('name', 'breed')
        return ()

    def save_model(self, request, obj, form, change):
        if change:
            data = {
                'id': obj.id,
                'name': obj.name,
                'breed': obj.breed,
                'salary': obj.salary,
            }
        else:
            data = {
                'name': form.cleaned_data.get('name'),
                'breed': form.cleaned_data.get('breed'),
                'salary': form.cleaned_data.get('salary'),
            }

        serializer = SpyCatsSerializer(instance=obj if change else None, data=data, partial=change)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            messages.success(
                request,
                "✅ SpyCat saved successfully through serializer validation."
            )
        except DRFValidationError as e:
            error_messages = []
            for field, errors in e.detail.items():
                for err in errors:
                    error_messages.append(f"{field}: {err}")
                    if field in form.fields:
                        form.add_error(field, str(err))
                    else:
                        form.add_error(None, f"{field}: {err}")
            error_text = "; ".join(error_messages)
            messages.error(request, f"❌ Validation error: {error_text}")

        except Exception as e:
            messages.error(request, f"❌ Unexpected error: {e}")
            raise

    def has_change_permission(self, request, obj=None):
        return True
