```bash
cd folio-feed
helm dependency build
helm dependency update
```

```bash
cd folio-feed
kubectl create namespace folio-feed
helm upgrade --install folio-feed -f values.yaml --namespace folio-feed . --debug
```

```bash
cd folio-feed
helm uninstall folio-feed --namespace folio-feed
kubectl delete pvc --all --namespace folio-feed
```