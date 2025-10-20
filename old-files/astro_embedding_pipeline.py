#!/usr/bin/env python3
"""
Astro-to-Text-to-Embedding Pipeline

This module creates a complete pipeline that:
1. Takes astronomical data from astroEncoder
2. Converts to rich natural language descriptions
3. Creates embeddings using sentence transformers
4. Stores in ChromaDB for semantic search
"""

import chromadb
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

# Add astroEncoder to path
sys.path.insert(0, str(Path(__file__).parent))
from astroEncoder import AstroEncoder


class AstroTextEncoder:
    """Converts astronomical data to natural language descriptions for embedding."""

    def __init__(self):
        # Vocabulary for natural language generation
        self.aspect_vocabulary = {
            'conjunction': [
                'conjunct', 'conjunction', 'together', 'merged with', 'aligned with',
                'tight conjunction', 'close together', 'in conjunction'
            ],
            'opposition': [
                'opposite', 'opposition', 'across from', 'opposing', 'in opposition',
                'facing', '180 degrees apart'
            ],
            'square': [
                'square', 'tension with', 'conflict with', 'challenging aspect',
                '90 degree tension', 'square aspect'
            ],
            'trine': [
                'trine', 'harmony with', 'flowing with', 'supportive aspect',
                '120 degree flow', 'harmonious trine'
            ],
            'sextile': [
                'sextile', 'opportunity with', 'cooperating with', 'supportive',
                '60 degree opportunity', 'productive aspect'
            ]
        }

        self.sign_descriptions = {
            'aries': ['Aries', 'Ram', 'fire sign', 'cardinal fire'],
            'taurus': ['Taurus', 'Bull', 'earth sign', 'fixed earth'],
            'gemini': ['Gemini', 'Twins', 'air sign', 'mutable air'],
            'cancer': ['Cancer', 'Crab', 'water sign', 'cardinal water'],
            'leo': ['Leo', 'Lion', 'fire sign', 'fixed fire'],
            'virgo': ['Virgo', 'Virgin', 'earth sign', 'mutable earth'],
            'libra': ['Libra', 'Scales', 'air sign', 'cardinal air'],
            'scorpio': ['Scorpio', 'Scorpion', 'water sign', 'fixed water'],
            'sagittarius': ['Sagittarius', 'Archer', 'fire sign', 'mutable fire'],
            'capricorn': ['Capricorn', 'Goat', 'earth sign', 'cardinal earth'],
            'aquarius': ['Aquarius', 'Water Bearer', 'air sign', 'fixed air'],
            'pisces': ['Pisces', 'Fish', 'water sign', 'mutable water']
        }

        self.degree_descriptions = {
            'early': ['early', 'beginning', 'initial', 'starting'],
            'middle': ['middle', 'mid', 'central', 'middle degrees'],
            'late': ['late', 'final', 'ending', 'concluding']
        }

    def create_aspect_descriptions(self, aspects: List) -> List[str]:
        """Convert aspects to multiple natural language descriptions."""
        descriptions = []

        # Focus on tight orbs (most important)
        major_aspects = [a for a in aspects if a.orb <= 8.0]
        major_aspects.sort(key=lambda x: x.orb)  # Tightest first

        for aspect in major_aspects[:10]:  # Top 10 aspects
            aspect_phrases = self.aspect_vocabulary.get(aspect.aspect_type, [aspect.aspect_type])

            for phrase in aspect_phrases[:3]:  # Use top 3 variations
                descriptions.extend([
                    f"{aspect.planet1} {phrase} {aspect.planet2}",
                    f"{aspect.planet1} {aspect.planet2} {phrase}",
                    f"{aspect.planet1} {phrase} {aspect.planet2} {aspect.orb:.1f} degree orb"
                ])

                # Add orb classification
                if aspect.orb <= 1.0:
                    descriptions.append(f"{aspect.planet1} {aspect.planet2} exact {phrase}")
                elif aspect.orb <= 3.0:
                    descriptions.append(f"{aspect.planet1} {aspect.planet2} tight {phrase}")
                elif aspect.orb <= 5.0:
                    descriptions.append(f"{aspect.planet1} {aspect.planet2} close {phrase}")

        return descriptions

    def create_planetary_descriptions(self, positions: Dict) -> List[str]:
        """Convert planetary positions to natural language."""
        descriptions = []

        # Prioritize important planets
        important_planets = ['jupiter', 'saturn', 'mars', 'venus', 'mercury']

        for planet in important_planets:
            if planet in positions:
                pos = positions[planet]
                sign_variations = self.sign_descriptions.get(pos.sign, [pos.sign])
                degree_variations = self.degree_descriptions.get(pos.degree_classification, [pos.degree_classification])

                # Create multiple descriptions for each planet
                for sign_desc in sign_variations[:2]:  # Use top 2 sign descriptions
                    for degree_desc in degree_variations[:2]:  # Use top 2 degree descriptions
                        descriptions.extend([
                            f"{planet} in {sign_desc}",
                            f"{planet} {degree_desc} {sign_desc}",
                            f"{planet} transiting {sign_desc}",
                            f"{planet} positioned in {degree_desc} {sign_desc}",
                            f"{planet} {pos.degree_in_sign:.1f} degrees {sign_desc}"
                        ])

        return descriptions

    def create_lunar_descriptions(self, astro_data) -> List[str]:
        """Create lunar phase and position descriptions."""
        descriptions = []

        # Lunar phase
        phase = astro_data.lunar_phase
        if 0 <= phase < 45:
            phase_names = ['new moon', 'dark moon', 'lunar new phase']
        elif 45 <= phase < 135:
            phase_names = ['waxing moon', 'growing moon', 'increasing moon']
        elif 135 <= phase < 225:
            phase_names = ['full moon', 'bright moon', 'lunar full phase']
        else:
            phase_names = ['waning moon', 'decreasing moon', 'dark phase approaching']

        for name in phase_names:
            descriptions.append(f"lunar phase {name}")
            descriptions.append(f"{name} energy")

        # Moon sign
        moon_pos = astro_data.positions.get('moon')
        if moon_pos:
            moon_signs = self.sign_descriptions.get(moon_pos.sign, [moon_pos.sign])
            for sign in moon_signs[:2]:
                descriptions.extend([
                    f"moon in {sign}",
                    f"lunar {sign} influence",
                    f"moon transiting {sign}"
                ])

        return descriptions

    def create_comprehensive_astro_text(self, astro_data) -> str:
        """Create comprehensive natural language description of astronomical data."""
        all_descriptions = []

        # 1. Major aspects (highest priority)
        aspect_descriptions = self.create_aspect_descriptions(astro_data.aspects)
        all_descriptions.extend(aspect_descriptions)

        # 2. Planetary positions
        planetary_descriptions = self.create_planetary_descriptions(astro_data.positions)
        all_descriptions.extend(planetary_descriptions)

        # 3. Lunar information
        lunar_descriptions = self.create_lunar_descriptions(astro_data)
        all_descriptions.extend(lunar_descriptions)

        # 4. Special configurations
        special_descriptions = self._detect_special_patterns(astro_data)
        all_descriptions.extend(special_descriptions)

        return " | ".join(all_descriptions)

    def _detect_special_patterns(self, astro_data) -> List[str]:
        """Detect special astronomical patterns and describe them."""
        descriptions = []

        # Multiple conjunctions
        conjunctions = [a for a in astro_data.aspects if a.aspect_type == 'conjunction' and a.orb <= 5.0]
        if len(conjunctions) >= 3:
            descriptions.append("multiple planetary conjunctions")
            descriptions.append("stellium formation")
            descriptions.append("concentrated planetary energy")

        # Grand trine detection (simplified)
        trines = [a for a in astro_data.aspects if a.aspect_type == 'trine' and a.orb <= 5.0]
        if len(trines) >= 3:
            descriptions.append("grand trine pattern")
            descriptions.append("harmonious triangle aspect")
            descriptions.append("flowing planetary energy")

        # T-square detection (simplified)
        squares = [a for a in astro_data.aspects if a.aspect_type == 'square' and a.orb <= 5.0]
        oppositions = [a for a in astro_data.aspects if a.aspect_type == 'opposition' and a.orb <= 5.0]
        if len(squares) >= 2 and len(oppositions) >= 1:
            descriptions.append("t-square tension pattern")
            descriptions.append("challenging aspect configuration")
            descriptions.append("dynamic tension formation")

        return descriptions


class AstroEmbeddingPipeline:
    """Complete pipeline from astroEncoder to ChromaDB storage."""

    def __init__(self, chroma_path: str = "./chroma_astro_db", model_name: str = 'all-MiniLM-L6-v2'):
        # Initialize components
        self.astro_encoder = AstroEncoder()
        self.text_encoder = AstroTextEncoder()

        # Initialize sentence transformer
        print(f"Loading sentence transformer model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self._setup_collections()

        print("✓ Astro embedding pipeline initialized")

    def _setup_collections(self):
        """Setup ChromaDB collections for different types of searches."""

        # Pure astronomical patterns
        self.astro_collection = self.chroma_client.get_or_create_collection(
            name="astronomical_patterns",
            metadata={"description": "Pure astronomical patterns for astro-specific queries"}
        )

        # Comprehensive astro descriptions (with redundancy for better matching)
        self.astro_detailed = self.chroma_client.get_or_create_collection(
            name="astronomical_detailed",
            metadata={"description": "Detailed astronomical descriptions with multiple phrasings"}
        )

        print("✓ ChromaDB collections initialized")

    def process_date(self, date: datetime, store_in_chroma: bool = True) -> Dict[str, Any]:
        """Process a single date through the complete pipeline."""
        date_str = date.strftime('%Y-%m-%d')
        print(f"Processing astronomical data for {date_str}...")

        # Step 1: Get astronomical data
        astro_data = self.astro_encoder.encode_date(date)

        # Step 2: Convert to natural language
        astro_text = self.text_encoder.create_comprehensive_astro_text(astro_data)

        # Step 3: Create embedding
        embedding = self.embedding_model.encode(astro_text)

        # Step 4: Store in ChromaDB
        if store_in_chroma:
            self._store_in_chromadb(date, astro_data, astro_text, embedding)

        result = {
            'date': date_str,
            'astro_data': astro_data,
            'text_description': astro_text,
            'embedding': embedding,
            'text_length': len(astro_text),
            'embedding_dimension': len(embedding)
        }

        print(f"✓ Processed {date_str}: {len(astro_text)} chars, {len(embedding)}D embedding")
        return result

    def _store_in_chromadb(self, date: datetime, astro_data, text: str, embedding: np.ndarray):
        """Store astronomical data in ChromaDB collections."""
        date_str = date.strftime('%Y-%m-%d')

        # Extract metadata for filtering
        major_conjunctions = [a for a in astro_data.aspects if a.aspect_type == 'conjunction' and a.orb <= 8.0]
        jupiter_pos = astro_data.positions.get('jupiter')
        saturn_pos = astro_data.positions.get('saturn')

        metadata = {
            'date': date_str,
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'conjunction_count': len(major_conjunctions),
            'jupiter_sign': jupiter_pos.sign if jupiter_pos else 'unknown',
            'saturn_sign': saturn_pos.sign if saturn_pos else 'unknown',
            'total_aspects': len(astro_data.aspects),
            'lunar_phase': float(astro_data.lunar_phase),
            'has_tight_aspects': len([a for a in astro_data.aspects if a.orb <= 3.0]) > 0
        }

        # Add conjunction details to metadata (ChromaDB doesn't accept lists, use string)
        if major_conjunctions:
            conj_pairs = [f"{c.planet1}-{c.planet2}" for c in major_conjunctions[:3]]
            metadata['major_conjunctions'] = ", ".join(conj_pairs)  # Convert to string

        # Store in detailed collection
        self.astro_detailed.upsert(
            documents=[text],
            embeddings=[embedding.tolist()],
            metadatas=[metadata],
            ids=[f"astro_detailed_{date_str}"]
        )

        # Create simplified version for pure astro collection
        simplified_text = self._create_simplified_text(astro_data)
        simplified_embedding = self.embedding_model.encode(simplified_text)

        self.astro_collection.upsert(
            documents=[simplified_text],
            embeddings=[simplified_embedding.tolist()],
            metadatas=[metadata],
            ids=[f"astro_{date_str}"]
        )

    def _create_simplified_text(self, astro_data) -> str:
        """Create simplified text focusing on key features."""
        parts = []

        # Top 3 tightest aspects only
        major_aspects = sorted([a for a in astro_data.aspects if a.orb <= 5.0], key=lambda x: x.orb)[:3]
        for aspect in major_aspects:
            parts.append(f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}")

        # Key planetary positions
        jupiter = astro_data.positions.get('jupiter')
        if jupiter:
            parts.append(f"Jupiter {jupiter.degree_classification} {jupiter.sign}")

        saturn = astro_data.positions.get('saturn')
        if saturn:
            parts.append(f"Saturn in {saturn.sign}")

        return " | ".join(parts)

    def batch_process(self, start_date: datetime, end_date: datetime,
                     max_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process multiple dates in batch."""
        print(f"Batch processing from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        results = []
        current_date = start_date
        day_count = 0

        while current_date <= end_date:
            if max_days and day_count >= max_days:
                break

            try:
                result = self.process_date(current_date)
                results.append(result)
                day_count += 1

                # Progress update
                if day_count % 30 == 0:
                    print(f"Processed {day_count} days...")

            except Exception as e:
                print(f"Error processing {current_date.strftime('%Y-%m-%d')}: {e}")

            current_date += timedelta(days=1)

        print(f"✓ Batch processing complete: {len(results)} days processed")
        return results

    def search_similar_patterns(self, query: str, collection_name: str = "astronomical_detailed",
                              n_results: int = 10, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for similar astronomical patterns."""
        print(f"Searching for: '{query}'")

        collection = getattr(self, f"{collection_name.split('_')[1]}_collection", self.astro_detailed)

        search_params = {
            'query_texts': [query],
            'n_results': n_results,
            'include': ['metadatas', 'documents', 'distances']
        }

        if filters:
            search_params['where'] = filters

        results = collection.query(**search_params)

        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'date': results['metadatas'][0][i].get('date'),
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'description': doc[:200] + "..." if len(doc) > 200 else doc,
                    'full_description': doc,
                    'metadata': results['metadatas'][0][i]
                })

        print(f"✓ Found {len(formatted_results)} similar patterns")
        return {
            'query': query,
            'results': formatted_results,
            'total_found': len(formatted_results)
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        astro_count = self.astro_collection.count()
        detailed_count = self.astro_detailed.count()

        return {
            'astronomical_patterns': astro_count,
            'astronomical_detailed': detailed_count,
            'total_embeddings': astro_count + detailed_count
        }


def main():
    """Demonstration of the astro embedding pipeline."""
    print("Astro-to-Text-to-Embedding Pipeline Demo")
    print("=" * 60)

    # Initialize pipeline
    pipeline = AstroEmbeddingPipeline()

    # Process some sample dates
    sample_dates = [
        datetime(2008, 9, 15, tzinfo=timezone.utc),  # Lehman collapse
        datetime(2020, 3, 23, tzinfo=timezone.utc),  # COVID crash
        datetime(2024, 1, 15, tzinfo=timezone.utc),  # Recent date
        datetime(2025, 6, 1, tzinfo=timezone.utc),   # Future date
    ]

    print("\n1. PROCESSING SAMPLE DATES")
    print("-" * 40)

    for date in sample_dates:
        result = pipeline.process_date(date)
        print(f"\n{result['date']}:")
        print(f"  Text: {result['text_description'][:100]}...")
        print(f"  Length: {result['text_length']} characters")
        print(f"  Embedding: {result['embedding_dimension']}D vector")

    print(f"\n2. COLLECTION STATISTICS")
    print("-" * 40)
    stats = pipeline.get_collection_stats()
    for collection, count in stats.items():
        print(f"  {collection}: {count} entries")

    print(f"\n3. SAMPLE QUERIES")
    print("-" * 40)

    # Test queries
    test_queries = [
        "Mercury Mars conjunction",
        "Jupiter in Cancer",
        "Saturn Neptune conjunction",
        "multiple planetary aspects",
        "tight orb conjunction"
    ]

    for query in test_queries:
        results = pipeline.search_similar_patterns(query, n_results=3)
        print(f"\nQuery: '{query}'")
        print(f"Found {results['total_found']} results:")

        for i, result in enumerate(results['results'][:2], 1):
            print(f"  {i}. {result['date']} (similarity: {result['similarity_score']:.3f})")
            print(f"     {result['description']}")

    print(f"\n✓ Pipeline demonstration complete!")


if __name__ == "__main__":
    main()