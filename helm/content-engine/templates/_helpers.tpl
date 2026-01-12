{{/*
Common labels
*/}}
{{- define "content-engine.labels" -}}
app.kubernetes.io/name: content-engine
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Build image name
*/}}
{{- define "content-engine.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- $image := .image -}}
{{- $tag := .tag | default "latest" -}}
{{- printf "%s/%s:%s" $registry $image $tag }}
{{- end }}
