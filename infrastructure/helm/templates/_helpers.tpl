{{- define "orderpilot.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "orderpilot.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "orderpilot.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "orderpilot.labels" -}}
app.kubernetes.io/name: {{ include "orderpilot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
