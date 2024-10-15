from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

# Create your views here
class HealthView(APIView):
    def get(self, request):
        response = {'message' : 'hello world'}
        return Response(response, status=status.HTTP_200_OK)