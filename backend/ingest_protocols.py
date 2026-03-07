
"""
Protocol Ingestion Script
Parses all PDFs in the 'protocols/' directory using the GeminiProtocolParser
and appends them to the system's protocol database.
"""

import sys
import os
import glob
import json
import asyncio
from typing import List

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gemini_parser import GeminiProtocolParser
from protocol_data import PROTOCOLS

# Directory containing new PDFs
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "protocols")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingested_protocols.json")

async def ingest_protocols():
    print(f"🚀 Ingesting protocols from: {PDF_DIR}")
    
    parser = GeminiProtocolParser()
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return

    ingested_data = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\n📄 Processing: {filename}...")
        
        try:
            # Run the parser (Directly await the async method)
            protocol_data = await parser.parse_pdf(pdf_path)
            
            # Add filename metadata
            protocol_data["source_filename"] = filename
            
            print(f"✅ Success! Parsed: {protocol_data.get('protocol_name')} ({protocol_data.get('protocol_code')})")
            
            # Simple validation check
            if "warnings" in protocol_data:
                print(f"   Warnings: {len(protocol_data['warnings'])}")
                
            ingested_data.append(protocol_data)
            
        except Exception as e:
            print(f"❌ Failed to parse {filename}: {e}")

    # Save all to a JSON file
    if ingested_data:
        print(f"\n💾 Saving {len(ingested_data)} protocols to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w") as f:
            json.dump(ingested_data, f, indent=2)
        print("✨ Ingestion Complete!")
    else:
        print("\n⚠️ No protocols were successfully parsed.")

if __name__ == "__main__":
    asyncio.run(ingest_protocols())
