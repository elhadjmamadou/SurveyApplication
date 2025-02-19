from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name,
                    password, **extra_fields):
        user = self.model(
            email=email, first_name=first_name,
            last_name=last_name, **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, first_name, last_name,
                         password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(
            email, first_name, last_name,
            password, **extra_fields
        )
