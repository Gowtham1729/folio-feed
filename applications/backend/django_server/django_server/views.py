from django.http import JsonResponse


def healthz(request):
    return JsonResponse({"status": "ok"})
