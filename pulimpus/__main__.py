"""A Python Pulumi program"""

import json
import pulumi
import pulumi_aws as aws_classic
import pulumi_aws_native as aws_native

# Create a class that encapsulates the functionality while subclassing the ComponentResource class (using the ComponentResource class as a template).
class OurBucketComponent(pulumi.ComponentResource):
    def __init__(self, name_me, policy_name='default', opts=None):
        # By calling super(), we ensure any instantiation of this class inherits from the ComponentResource class so we don't have to declare all the same things all over again.
        super().__init__('pkg:index:OurBucketComponent', name, None, opts)
        # This definition ensures the new component resource acts like anything else in the Pulumi ecosystem when being called in code.
        child_opts = pulumi.ResourceOptions(parent=self)
        self.name_me = name_me
        self.policy_name = policy_name
        self.bucket = aws_native.s3.Bucket(f"{self.name_me}")
        self.policy_list = {
            'default': default,
            'locked': '{...}',
            'permissive': '{...}'
        }
        # We also need to register all the expected outputs for this component resource that will get returned by default.
        self.register_outputs({
            "bucket_name": self.bucket.bucket_name
        })

    def define_policy(self):
        policy_name = self.policy_name
        try:
            json_data = self.policy_list[f"{policy_name}"]
            policy = self.bucket.arn.apply(lambda arn: json.dumps(json_data).replace('fakeobjectresourcething', arn))
            return policy
        except KeyError as err:
            add_note = "Policy name needs to be 'default', 'locked', or 'permissive'"
            print(f"Error: {add_note}. You used {policy_name}.")
            raise

    def set_policy(self):
        bucket_policy = aws_classic.s3.BucketPolicy(
            f"{self.name_me}-policy",
            bucket=self.bucket.id,
            policy=self.define_policy(),
            opts=pulumi.ResourceOptions(parent=self.bucket)
        )
        return bucket_policy

bucket1 = OurBucketClass('laura-bucket-1', 'default')
bucket1.set_policy()

pulumi.export("bucket_name", bucket1.bucket.id)