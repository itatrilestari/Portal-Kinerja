from apps.api.models import Log

def create_log(user, action, feature_name, message):
    log = Log.objects.create(user=user, action=action, feature_name=feature_name, message=message)
    return log