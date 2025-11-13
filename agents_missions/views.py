from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import SpyMission
from .serializers import SpyMissionSerializer

class SpyMissionViewSet(viewsets.ModelViewSet):
    queryset = SpyMission.objects.all()
    serializer_class = SpyMissionSerializer

    def destroy(self, request, *args, **kwargs):
        mission = self.get_object()
        if mission.agent is not None:
            return Response(
                {"detail": "Cannot delete a mission assigned to a cat."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
