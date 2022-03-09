"""A Python Pulumi program"""

import pulumi

config = pulumi.Config()
stack = pulumi.get_stack()
org = config.require("org")

stack_ref = pulumi.StackReference(f"{org}/my-first-app/{stack}")

pulumi.export("shopUrl", stack_ref.get_output("url"))