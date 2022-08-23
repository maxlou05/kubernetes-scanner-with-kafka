# ncyd-nf-scanning

Scans Kubernetes cluster for changes in namespace, and matches the namespaces with network functions.
When change is detected, sends it to Kafka, which is also located on the cluster.
