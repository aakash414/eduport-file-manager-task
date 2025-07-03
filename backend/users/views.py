from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer

class RegisterView(views.APIView):
    permission_classes = [AllowAny] # Anyone can register

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(
            {
                "user": serializer.data,
                "message": "Registration successful. You are now logged in."
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(views.APIView):
    permission_classes = [AllowAny] # Anyone can attempt to log in

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "message": "Login successful."
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'Invalid Credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can log out

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(
            {"message": "You have been successfully logged out."},
            status=status.HTTP_200_OK
        )

class UserView(views.APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can view their data

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)
