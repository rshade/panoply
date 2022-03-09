"""A Python Pulumi program"""

import os
import pulumi
import pulumi_docker as docker
from pulumi import Output

# get configuration
config = pulumi.Config()
frontend_port = config.require_int("frontend_port")
backend_port = config.require_int("backend_port")
mongo_port = config.require_int("mongo_port")
mongo_host = config.require("mongo_host") # Note that strings are the default, so it's not `config.require_str`, just `config.require`.
mongo_username = config.require("mongo_username")
mongo_password = config.require_secret("mongo_password")
database = config.require("database")
node_environment = config.require("node_environment")

stack = pulumi.get_stack()

# build our backend image!
backend_image_name = "backend"
backend = docker.Image(backend_image_name,
                        build=docker.DockerBuild(context=f"{os.getcwd()}/app/backend"),
                        image_name=f"{backend_image_name}:{stack}",
                        skip_push=True
                        )

frontend_image_name = "frontend"
frontend = docker.Image(frontend_image_name,
                        build=docker.DockerBuild(context=f"{os.getcwd()}/app/frontend"),
                        image_name=f"{frontend_image_name}:{stack}",
                        skip_push=True
                        )

# build our mongodb image!
mongo_image = docker.RemoteImage("mongo", name="mongo:bionic")

network = docker.Network("network", name=f"services-{stack}")

# create the mongo container!
mongo_container = docker.Container("mongo_container",
                        image=mongo_image.repo_digest,
                        name=f"mongo-{stack}",
                        ports=[docker.ContainerPortArgs(
                          internal=mongo_port,
                          external=mongo_port
                        )],
                        networks_advanced=[docker.ContainerNetworksAdvancedArgs(
                            name=network.name,
                            aliases=["mongo"]
                        )],
                        envs=[
                                f"MONGO_INITDB_ROOT_USERNAME={mongo_username}",
                                mongo_password.apply(lambda password: f"MONGO_INITDB_ROOT_PASSWORD={password}")
                        ]
                      )

# create the backend container!
backend_container = docker.Container("backend_container",
                        name=f"backend-{stack}",
                        image=backend.base_image_name,
                        ports=[docker.ContainerPortArgs(
                            internal=backend_port,
                            external=backend_port)],
                        envs=[
                            Output.concat(
                                "DATABASE_HOST=mongodb://",
                                mongo_username,
                                ":",
                                config.require_secret("mongo_password"),
                                "@",
                                mongo_host,
                                ":",
                                f"{mongo_port}",
                            ), #Changed!
                            f"DATABASE_NAME={database}",
                            f"NODE_ENV={node_environment}"
                        ],
                        networks_advanced=[docker.ContainerNetworksAdvancedArgs(
                            name=network.name
                        )],
                        opts=pulumi.ResourceOptions(depends_on=[mongo_container])
                        )

data_seed_container = docker.Container("data_seed_container",
                                       image=mongo_image.repo_digest,
                                       name="data_seed",
                                       must_run=False,
                                       rm=True,
                                       opts=pulumi.ResourceOptions(depends_on=[mongo_container, backend_container]),
                                       mounts=[docker.ContainerMountArgs(
                                           target="/home/products.json",
                                           type="bind",
                                           source=f"{os.getcwd()}/products.json"
                                       )],
                                       command=[ # This is the changed part!
                                           "sh", "-c",
                                           pulumi.Output.concat(
                                               "mongoimport --host ",
                                               mongo_host,
                                               " -u ",
                                               mongo_username,
                                               " -p ",
                                               config.require_secret("mongo_password"),
                                               " --authenticationDatabase admin --db cart --collection products --type json --file /home/products.json --jsonArray"
                                           )
                                       ],
                                       networks_advanced=[docker.ContainerNetworksAdvancedArgs(
                                           name=network.name
                                       )]
                                       )
# create the frontend container!
frontend_container = docker.Container("frontend_container",
                                      image=frontend.base_image_name,
                                      name=f"frontend-{stack}",
                                      ports=[docker.ContainerPortArgs(
                                          internal=frontend_port,
                                          external=frontend_port
                                      )],
                                      envs=[
                                          f"LISTEN_PORT={frontend_port}",
                                          f"HTTP_PROXY=backend-{stack}:{backend_port}"
                                      ],
                                      networks_advanced=[docker.ContainerNetworksAdvancedArgs(
                                          name=network.name
                                      )]
                                      )
pulumi.export("url", f"http://localhost:{frontend_port}")
pulumi.export("mongo_password", mongo_password)