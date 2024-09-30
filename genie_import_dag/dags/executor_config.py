import kubernetes.client as k8s

k8s_executor_config = {
    "pod_override": k8s.V1Pod(
        spec=k8s.V1PodSpec(
            containers=[
                k8s.V1Container(
                    name="base",
                    image="callachennault/airflow-worker-genie:0.1",
                    # TODO maybe we should move all of the volume mounts to here too
                    # volume_mounts=[
                    #     k8s.V1VolumeMount(mount_path="/opt/airflow/git_repos", name="pv", read_only=False),
                    #     k8s.V1VolumeMount(mount_path="/opt/airflow/secrets", name="gcp-keyfile", read_only=True),
                    #     k8s.V1VolumeMount(mount_path="/home/airflow/.ssh", name="git-secret", read_only=True),
                    # ]
                    resources=k8s.V1ResourceRequirements(
                        requests={"cpu": "500m", "memory": "4Gi"},
                        limits={"cpu": "4", "memory": "32Gi"}
                    )
                )
            ]
        )
    )
}