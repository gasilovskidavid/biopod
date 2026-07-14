resource "aws_key_pair" "admin" {
  key_name   = "biopod-admin-key"
  public_key = var.ssh_public_key
}
