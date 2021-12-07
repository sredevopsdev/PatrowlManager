from .models import Alert
from findings.models import Finding
from assets.models import Asset
from rules.models import Rule


def _evaluate_alert_rules(finding, highest_severity="info"):
    """Evaluate custom alert rules on findings."""
    rules = Rule.objects.filter(
        enabled=True,
        scope__in=['finding', 'asset', 'scan'],
        trigger='auto',
        target='alert')

    severities = {
        'info': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }

    for rule in rules:
        rck, rcv = list(rule.condition.items())[0]
        field = ""
        if rule.scope == "asset":
            field = "asset__"
        elif rule.scope == "scan":
            field = "scan__"
        kwargs = {
            "id": finding.id,
            field + rule.scope_attr + rck: rcv
        }
        if Finding.objects.filter(**kwargs).first() is not None:
            if severities[rule.severity.lower()] > severities[highest_severity]:
                highest_severity = rule.severity.lower()
        # for rf in Finding.objects.filter(**kwargs):
        #     rule.notify(message="[Rule={}]".format(rule.title), asset=finding.asset, description=finding.description, finding=rf)
    return highest_severity


def generate_finding_alert(finding_id, scan_id, severity="info", action="new_finding"):
    """Generate an alert when a new finding is found."""
    actions = {
        "new_finding": {
            "message": "New finding found",
            "type": "new_finding",
        },
        "missing_finding": {
            "message": "Missing finding from scan",
            "type": "missing_finding",
        },
        "reopened_finding": {
            "message": "Finding reopened. Considered as closed but a recent scan found it again",
            "type": "reopened_finding",
        },
    }

    if action not in actions.keys():
        return None

    alert_message = actions[action]['message']
    alert_type = actions[action]['type']

    # finding = Finding.objects.filter(id=finding_id, status="new").first()
    finding = Finding.objects.filter(id=finding_id).first()
    if finding is None:
        return None

    # Set default severity
    if severity not in ['info', 'low', 'medium', 'high', 'critical']:
        severity = 'info'
    severity = _evaluate_alert_rules(finding, severity)

    asset_id = None
    asset_type = None
    asset = Asset.objects.filter(value=finding.asset_name).first()
    if asset is not None:
        asset_id = asset.id
        asset_type = asset.type

    alert = Alert.objects.create(
        message=alert_message,
        type=alert_type,
        status='new',
        severity=severity,
        metadata={
            "finding_id": finding.id,
            "finding_title": finding.title,
            "finding_description": finding.description,
            "finding_tags": finding.tags,
            "scan_id": scan_id,
            "scan_definition_id": finding.scan.scan_definition.id,
            "asset_name": finding.asset_name,
            "asset_type": asset_type,
            "asset_id": asset_id,
            "asset_tags": [t.value for t in finding.asset.categories.all()],
        },
        owner=finding.owner
    )
    if finding.asset.teams.count() > 0:
        for team in finding.asset.teams.all():
            alert.teams.add(team)
        alert.save()

    return alert

#
# def new_finding_alert(finding_id, scan_id, severity="info"):
#     """Generate an alert when a new finding is found."""
#     finding = Finding.objects.filter(id=finding_id, status="new").first()
#     if finding is None:
#         return None
#
#     # Set default severity
#     if severity not in ['info', 'low', 'medium', 'high', 'critical']:
#         severity = 'info'
#
#     asset_id = None
#     asset = Asset.objects.filter(value=finding.asset_name).first()
#     if asset is not None:
#         asset_id = asset.id
#
#     alert = Alert.objects.create(
#         message="New finding",
#         type="new_finding",
#         status='new',
#         severity=severity,
#         metadata={
#             "finding_id": finding.id,
#             "finding_title": finding.title,
#             "finding_tags": finding.tags,
#             "scan_id": scan_id,
#             "scan_definition_id": finding.scan.scan_definition.id,
#             "asset_name": finding.asset_name,
#             "asset_id": asset_id,
#             "asset_tags": [t.value for t in finding.asset.categories.all()],
#         },
#         owner=finding.owner
#     )
#     if finding.asset.teams.count() > 0:
#         for team in finding.asset.teams.all():
#             alert.teams.add(team)
#         alert.save()
#
#     return alert
#
#
# def missing_finding_alert(finding_id, scan_id, severity="info"):
#     """Generate an alert when a finding is missing from previous scan."""
#     finding = Finding.objects.filter(id=finding_id).first()
#     if finding is None:
#         return None
#
#     # Set default severity
#     if severity not in ['info', 'low', 'medium', 'high', 'critical']:
#         severity = 'info'
#
#     asset_id = None
#     asset = Asset.objects.filter(value=finding.asset_name).first()
#     if asset is not None:
#         asset_id = asset.id
#
#     alert = Alert.objects.create(
#         message="Missing finding",
#         type="missing_finding",
#         status='new',
#         severity=severity,
#         metadata={
#             "finding_id": finding.id,
#             "finding_title": finding.title,
#             "finding_tags": finding.tags,
#             "scan_id": scan_id,
#             "scan_definition_id": finding.scan.scan_definition.id,
#             "asset_name": finding.asset_name,
#             "asset_id": asset_id,
#             "asset_tags": [t.value for t in finding.asset.categories.all()],
#         },
#         owner=finding.owner
#     )
#     if finding.asset.teams.count() > 0:
#         for team in finding.asset.teams.all():
#             alert.teams.add(team)
#         alert.save()
#     return alert
#
#
# def reopened_finding_alert(finding_id, scan_id, severity="info"):
#     """Generate an alert when a finding is found again (after being closed)."""
#     finding = Finding.objects.filter(id=finding_id).first()
#     if finding is None:
#         return None
#
#     # Set default severity
#     if severity not in ['info', 'low', 'medium', 'high', 'critical']:
#         severity = 'info'
#
#     asset_id = None
#     asset = Asset.objects.filter(value=finding.asset_name).first()
#     if asset is not None:
#         asset_id = asset.id
#
#     alert = Alert.objects.create(
#         message="Finding reopened. Considered as closed but a recent scan found it again",
#         type="reopened_finding",
#         status='new',
#         severity=severity,
#         metadata={
#             "finding_id": finding.id,
#             "finding_title": finding.title,
#             "finding_tags": finding.tags,
#             "scan_id": scan_id,
#             "scan_definition_id": finding.scan.scan_definition.id,
#             "asset_name": finding.asset_name,
#             "asset_id": asset_id,
#             "asset_tags": [t.value for t in finding.asset.categories.all()],
#         },
#         owner=finding.owner
#     )
#     if finding.asset.teams.count() > 0:
#         for team in finding.asset.teams.all():
#             alert.teams.add(team)
#         alert.save()
#     return alert
