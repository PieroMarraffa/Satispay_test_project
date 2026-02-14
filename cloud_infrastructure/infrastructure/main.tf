module "cloud_resources" {
  source = "./resources"
  tags   = module.tags.tags
  s3_website_uri = var.test_via_ui ? module.s3_website[0].website_url : null
  test_via_ui = var.test_via_ui
}

module "tags" {
  source = "../tags/test"
}

module "s3_website" {
  count = var.test_via_ui ? 1 : 0

  source = "./s3_website/terraform"

  tags   = module.tags.tags
}