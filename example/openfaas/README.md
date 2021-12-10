The openfaas template files were created by pulling these configurations like this:

    helm repo add openfaas https://openfaas.github.io/faas-netes/
    helm template openfaas openfaas/openfaas \
      --namespace openfaas \
      --set functionNamespace=openfaas-fn \
      --set basic_auth=false \
      --set async=false \
      --set exposeServices=false \
      --set faasnetes.httpProbe=true \
      --set faasIdler.create=false
