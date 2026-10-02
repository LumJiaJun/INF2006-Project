import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INFRASTRUCTURE = ROOT / "src" / "infrastructure"


class InfrastructureSecurityTests(unittest.TestCase):
    def test_private_routes_require_jwt_authorization(self):
        terraform = "\n".join(
            (INFRASTRUCTURE / name).read_text(encoding="utf-8")
            for name in ("history.tf", "chat.tf")
        )
        for route in ("POST /predictions", "GET /history", "POST /chat"):
            block = re.search(
                rf'resource "aws_apigatewayv2_route" "[^"]+" {{(?:(?!\n}}).)*route_key\s*=\s*"{re.escape(route)}"(?:(?!\n}}).)*\n}}',
                terraform,
                re.DOTALL,
            )
            self.assertIsNotNone(block, route)
            self.assertIn('authorization_type = "JWT"', block.group(0))
            self.assertIn("authorizer_id", block.group(0))

    def test_lambda_egress_is_not_internet_wide(self):
        network = (INFRASTRUCTURE / "network.tf").read_text(encoding="utf-8")
        lambda_group = network.split('resource "aws_security_group" "lambda"', 1)[1].split(
            'resource "aws_security_group" "endpoint"', 1
        )[0]
        self.assertNotIn('cidr_blocks = ["0.0.0.0/0"]', lambda_group)
        self.assertIn("aws_vpc.lambda.cidr_block", lambda_group)
        self.assertIn("aws_vpc_endpoint.s3.prefix_list_id", lambda_group)
        self.assertIn("aws_vpc_endpoint.dynamodb.prefix_list_id", lambda_group)

    def test_each_lambda_has_a_purpose_specific_role(self):
        role_names = []
        for path in INFRASTRUCTURE.glob("*.tf"):
            text = path.read_text(encoding="utf-8")
            role_names.extend(re.findall(r'resource "aws_iam_role" "([^"]+_lambda)"', text))
        self.assertEqual(
            sorted(role_names),
            ["analytics_lambda", "chat_lambda", "health_lambda", "history_lambda", "prediction_lambda"],
        )


if __name__ == "__main__":
    unittest.main()
