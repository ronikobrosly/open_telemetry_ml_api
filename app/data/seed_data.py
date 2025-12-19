import json
import hashlib

CATEGORIES = {
    "machine_learning": [
        "neural networks", "deep learning", "supervised learning",
        "unsupervised learning", "reinforcement learning", "gradient descent",
        "backpropagation", "convolutional networks", "transformers", "model training"
    ],
    "data_science": [
        "data analysis", "statistical modeling", "data visualization",
        "pandas", "numpy", "exploratory analysis", "hypothesis testing",
        "regression analysis", "time series", "feature engineering"
    ],
    "web_development": [
        "javascript frameworks", "react", "vue", "angular", "REST APIs",
        "GraphQL", "web security", "responsive design", "progressive web apps",
        "server-side rendering"
    ],
    "cloud_computing": [
        "AWS services", "Azure cloud", "Google Cloud Platform", "kubernetes",
        "docker containers", "serverless architecture", "cloud storage",
        "load balancing", "auto scaling", "cloud security"
    ],
    "cybersecurity": [
        "network security", "encryption", "authentication", "authorization",
        "penetration testing", "vulnerability assessment", "security protocols",
        "firewalls", "intrusion detection", "security compliance"
    ]
}

def generate_seed_documents():
    """Generate deterministic seed documents"""
    documents = []
    doc_counter = 1

    for category, topics in CATEGORIES.items():
        for i, topic in enumerate(topics):
            doc_id = f"{category[:3].upper()}{doc_counter:03d}"

            # Generate deterministic embedding (8-dim for simplicity)
            seed_str = f"{category}_{topic}_{i}"
            hash_obj = hashlib.md5(seed_str.encode())
            hash_bytes = hash_obj.digest()
            embedding = [
                (hash_bytes[j] / 255.0) * 2 - 1  # Normalize to [-1, 1]
                for j in range(8)
            ]

            title = topic.title()
            text = f"This document covers {topic} in the context of {category.replace('_', ' ')}. " \
                   f"It provides comprehensive information about {topic} concepts, " \
                   f"best practices, and real-world applications. " \
                   f"Key aspects include implementation details, common patterns, and expert insights."

            documents.append({
                "doc_id": doc_id,
                "title": title,
                "text": text,
                "category": category,
                "embedding": json.dumps(embedding)
            })

            doc_counter += 1

    return documents
