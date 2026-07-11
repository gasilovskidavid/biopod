resource "aws_key_pair" "admin" {
  key_name   = "biopod-admin-key"
  public_key = file(pathexpand("~/.ssh/id_ed25519.pub"))
}
