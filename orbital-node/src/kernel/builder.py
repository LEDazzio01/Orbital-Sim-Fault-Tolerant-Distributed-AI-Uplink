"""
Semantic Kernel Builder for Azure OpenAI Integration.
This module handles the initialization of the AI processing pipeline.
"""
import os
from typing import Optional

# Try to import semantic_kernel, gracefully degrade if not available
try:
    import semantic_kernel as sk
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
    SK_AVAILABLE = True
except ImportError:
    SK_AVAILABLE = False
    print(">> WARNING: semantic_kernel not installed. AI features disabled.")


def build_kernel():
    """
    Build and configure the Semantic Kernel with Azure OpenAI.
    Returns None if credentials are not configured or SK is not available.
    """
    if not SK_AVAILABLE:
        return None
    
    # Get Azure OpenAI credentials from environment
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    if not api_key or not endpoint:
        print(">> WARNING: Azure OpenAI credentials not configured.")
        return None
    
    try:
        # Initialize the kernel
        kernel = sk.Kernel()
        
        # Add Azure OpenAI chat service
        kernel.add_service(
            AzureChatCompletion(
                service_id="azure_chat",
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key
            )
        )
        
        return kernel
    except Exception as e:
        print(f">> ERROR: Failed to initialize Semantic Kernel: {e}")
        return None
