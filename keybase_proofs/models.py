from django.db import models
from django.utils import timezone

from .users import UserModelString


class KeybaseProof(models.Model):
    """
    A simple model which stores keybase proofs for users.  A user can have
    multiple keybase proofs for different keybase users.
    """
    user = models.ForeignKey(
        UserModelString(),
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(default=timezone.now)
    kb_username = models.CharField(max_length=128)
    sig_hash = models.CharField(max_length=66)
    # Flag indicating if the profile page should display this proof. Set once
    # the keybase servers have verified it.
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'kb_username'),)

    def to_dict(self):
        """
        Serialization format for the list api.
        """
        return {
            'kb_username': self.kb_username,
            'sig_hash': self.sig_hash,
        }

    def __str__(self):
        return '<KeybaseProof username:{}, kb_username:{}, sig_hash:{}, is_verified:{}'.format(
            self.user.username,
            self.kb_username,
            self.sig_hash,
            self.is_verified,
        )
