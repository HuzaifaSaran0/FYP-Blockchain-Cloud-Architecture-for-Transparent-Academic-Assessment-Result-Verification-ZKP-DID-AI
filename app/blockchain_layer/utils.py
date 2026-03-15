import hashlib
import uuid
from django.utils import timezone


def _sha256(data: str) -> str: 
    """Helper function to compute SHA-256 hash of a string where SHA-256 is a cryptographic hash function that produces a fixed-size 256-bit (32-byte) hash value from input data. It is widely used for data integrity verification and digital signatures."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def get_next_block_number() -> int:
    from blockchain_layer.models import BlockchainRecord
    last = BlockchainRecord.objects.order_by("-block_number").first()
    return (last.block_number + 1) if last else 1


def create_blockchain_record(
    record_type: str,
    related_student: str = None,
    related_exam: str = None,
    extra_data: str = "",
):
    """
    Creates and returns a BlockchainRecord with a deterministic
    transaction hash and auto-incremented block number.
    """
    from blockchain_layer.models import BlockchainRecord

    timestamp = timezone.now().isoformat()
    # Add uuid4 entropy to ensure uniqueness even for identical inputs
    entropy = uuid.uuid4().hex
    tx_input = f"{record_type}:{related_student}:{related_exam}:{timestamp}:{entropy}"
    transaction_hash = _sha256(tx_input)
    data_hash = _sha256(f"{related_student}:{related_exam}:{extra_data}")
    block_number = get_next_block_number()

    return BlockchainRecord.objects.create(
        record_type=record_type,
        related_student=related_student,
        related_exam=related_exam,
        transaction_hash=transaction_hash,
        block_number=block_number,
        data_hash=data_hash,
        verification_status="unverified",
    )
