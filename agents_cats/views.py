from rest_framework import viewsets
from .models import SpyCats
from .serializers import SpyCatsSerializer

class SpyCatsViewSet(viewsets.ModelViewSet):
    queryset = SpyCats.objects.all()
    serializer_class = SpyCatsSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = {'salary': request.data.get('salary', instance.salary)}
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self.retrieve(request, *args, **kwargs)