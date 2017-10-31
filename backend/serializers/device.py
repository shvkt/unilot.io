from pprint import pprint

from push_notifications.models import APNSDevice, GCMDevice
from rest_framework import serializers
from django.utils.translation import ugettext as _
from push_notifications.gcm import send_message as gcm_send_message


class DeviceOS:
    IOS = 10
    ANDROID = 20

    LIST = (IOS, ANDROID)

    CHOICES = (
        (IOS, _('IOS')),
        (ANDROID, _('Android OS'))
    )


class DummyDeviceObject(object):
    def __init__(self, registration_id, cloud_message_type=None):
        self.os = DeviceOS.IOS if cloud_message_type is None else DeviceOS.ANDROID
        self.token = registration_id


class CreateDeviceSerializer(serializers.Serializer):

    os    = serializers.ChoiceField(choices=DeviceOS.CHOICES)
    token = serializers.CharField()

    def create(self, validated_data):
        device_data = {
            'registration_id': validated_data.get('token', None)
        }

        if int(validated_data.get('os', '')) not in DeviceOS.LIST:
            raise AttributeError(('Invalid value "%s" of os field') % (validated_data.get('os')))

        if validated_data.get('os') == 10:
            APNSDevice.objects.get_or_create(**device_data)
        else:
            device_data['cloud_message_type'] = 'FCM'
            GCMDevice.objects.get_or_create(**device_data)

        # Pretty dirty hack to keep back compatibility
        instance = DummyDeviceObject(**device_data)

        return instance

class DebugPush(serializers.Serializer):
    os = serializers.ChoiceField(choices=DeviceOS.CHOICES)
    token = serializers.CharField(required=True)
    message = serializers.CharField(required=False)
    payload = serializers.DictField(required=True)

    def save(self, **kwargs):
        device_data = {}

        if self.validated_data['os'] == DeviceOS.IOS:
            device_class = APNSDevice
        else:
            device_data['cloud_message_type'] = 'FCM'
            device_class = GCMDevice

        device_data['registration_id'] = self.validated_data['token']

        device, created = device_class.objects.get_or_create(**device_data)

        device.send_message(message=None, extra=self.validated_data.get('payload', {}))
