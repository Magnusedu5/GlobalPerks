from rest_framework import serializers

VALID_SERVICES = ['portraits', 'headshots', 'maternity', 'events', 'brand']

class BookingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    service = serializers.ChoiceField(choices=VALID_SERVICES)
    preferred_date = serializers.DateField()
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        default=''
    )
