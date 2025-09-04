from django.db import models


class DomainRank(models.Model):
    """Simple domain ranking model - only stores domains with rank and processing status"""
    
    domain = models.CharField(max_length=255, unique=True, db_index=True)  # example.com (no protocol)
    rank = models.PositiveIntegerField(default=0, db_index=True)  # Number of external links pointing to this domain
    processed = models.BooleanField(default=False, db_index=True)  # Has this domain been crawled for outgoing links?
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rank', 'processed', 'domain']  # Sort by rank desc, unprocessed first
        indexes = [
            models.Index(fields=['-rank', 'processed']),  # For efficient querying
        ]
    
    def __str__(self):
        status = "✅" if self.processed else "⏳"
        return f"{status} {self.domain} (rank: {self.rank})"
