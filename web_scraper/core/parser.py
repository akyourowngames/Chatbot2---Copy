"""
🧠 AI-POWERED PARSER — The Brain of the Machine 🧬
Advanced content extraction and understanding using AI models for intelligent parsing.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup, Tag
import requests
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime
import openai
import cohere
from transformers import pipeline
import spacy
from newspaper import Article
import dateutil.parser
import pytz

@dataclass
class ParsedContent:
    """Structured data extracted from web content"""
    url: str
    title: str
    content: str
    summary: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: List[str] = None
    entities: Dict[str, List[str]] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    word_count: int = 0
    reading_time: int = 0
    images: List[str] = None
    links: List[str] = None
    metadata: Dict[str, Any] = None
    extracted_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.entities is None:
            self.entities = {}
        if self.images is None:
            self.images = []
        if self.links is None:
            self.links = []
        if self.metadata is None:
            self.metadata = {}
        if self.extracted_at is None:
            self.extracted_at = datetime.now().isoformat()

@dataclass
class ParserConfig:
    """Configuration for AI parser"""
    use_openai: bool = True
    use_cohere: bool = False
    use_local_models: bool = True
    openai_api_key: str = None
    cohere_api_key: str = None
    max_content_length: int = 50000
    extract_images: bool = True
    extract_links: bool = True
    extract_entities: bool = True
    extract_sentiment: bool = True
    extract_language: bool = True
    summarize_content: bool = True
    chunk_size: int = 4000

class AIParser:
    """
    🧠 AI-powered content parser with multiple model support
    """
    
    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()
        self.soup = None
        self.content_hash = None
        
        # Initialize AI models
        self._init_ai_models()
        
        # Initialize NLP models
        self._init_nlp_models()
        
        # Initialize newspaper for article extraction
        self.article_extractor = Article
        
    def _init_ai_models(self):
        """Initialize AI models for content understanding"""
        try:
            if self.config.use_openai and self.config.openai_api_key:
                openai.api_key = self.config.openai_api_key
                self.openai_available = True
            else:
                self.openai_available = False
                
            if self.config.use_cohere and self.config.cohere_api_key:
                self.cohere_client = cohere.Client(self.config.cohere_api_key)
                self.cohere_available = True
            else:
                self.cohere_available = False
                
        except Exception as e:
            logging.warning(f"⚠️ AI models initialization failed: {e}")
            self.openai_available = False
            self.cohere_available = False
    
    def _init_nlp_models(self):
        """Initialize local NLP models"""
        try:
            if self.config.use_local_models:
                # Load spaCy model for NER
                self.nlp = spacy.load("en_core_web_sm")
                
                # Load sentiment analysis pipeline
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                
                # Load summarization pipeline
                self.summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn"
                )
                
                self.local_models_available = True
            else:
                self.local_models_available = False
                
        except Exception as e:
            logging.warning(f"⚠️ Local NLP models initialization failed: {e}")
            self.local_models_available = False
    
    def parse_html(self, html_content: str, url: str = "") -> ParsedContent:
        """
        🧬 Parse HTML content and extract structured data
        """
        try:
            # Create BeautifulSoup object
            self.soup = BeautifulSoup(html_content, 'html.parser')
            
            # Generate content hash for caching
            self.content_hash = hashlib.md5(html_content.encode()).hexdigest()
            
            # Extract basic content using newspaper
            article_data = self._extract_with_newspaper(html_content, url)
            
            # Extract additional data with BeautifulSoup
            enhanced_data = self._extract_with_beautifulsoup(url)
            
            # Merge the data
            parsed_content = self._merge_extracted_data(article_data, enhanced_data, url)
            
            # Apply AI enhancements
            parsed_content = self._apply_ai_enhancements(parsed_content)
            
            logging.info(f"🧠 Parsed content from {url}: {parsed_content.word_count} words")
            
            return parsed_content
            
        except Exception as e:
            logging.error(f"❌ Failed to parse HTML content: {e}")
            return self._create_empty_content(url)
    
    def _extract_with_newspaper(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract content using newspaper library"""
        try:
            article = self.article_extractor(url)
            article.set_html(html_content)
            article.parse()
            
            return {
                'title': article.title,
                'content': article.text,
                'author': article.authors[0] if article.authors else None,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'images': article.images,
                'summary': article.summary
            }
            
        except Exception as e:
            logging.warning(f"⚠️ Newspaper extraction failed: {e}")
            return {}
    
    def _extract_with_beautifulsoup(self, url: str) -> Dict[str, Any]:
        """Extract additional data using BeautifulSoup"""
        data = {
            'images': [],
            'links': [],
            'metadata': {}
        }
        
        try:
            # Extract images
            if self.config.extract_images:
                img_tags = self.soup.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        full_url = urljoin(url, src)
                        data['images'].append(full_url)
            
            # Extract links
            if self.config.extract_links:
                link_tags = self.soup.find_all('a', href=True)
                for link in link_tags:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        data['links'].append(full_url)
            
            # Extract metadata
            meta_tags = self.soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    data['metadata'][name] = content
            
            # Extract title if not found
            if not data.get('title'):
                title_tag = self.soup.find('title')
                if title_tag:
                    data['title'] = title_tag.get_text().strip()
            
        except Exception as e:
            logging.warning(f"⚠️ BeautifulSoup extraction failed: {e}")
        
        return data
    
    def _merge_extracted_data(self, article_data: Dict, enhanced_data: Dict, url: str) -> ParsedContent:
        """Merge data from different extraction methods"""
        
        # Calculate word count and reading time
        content = article_data.get('content', '')
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # Average reading speed
        
        return ParsedContent(
            url=url,
            title=article_data.get('title', enhanced_data.get('title', '')),
            content=content,
            summary=article_data.get('summary', ''),
            author=article_data.get('author'),
            publish_date=article_data.get('publish_date'),
            images=enhanced_data.get('images', []),
            links=enhanced_data.get('links', []),
            metadata=enhanced_data.get('metadata', {}),
            word_count=word_count,
            reading_time=reading_time
        )
    
    def _apply_ai_enhancements(self, content: ParsedContent) -> ParsedContent:
        """Apply AI enhancements to extracted content"""
        
        # Extract entities using spaCy
        if self.config.extract_entities and self.local_models_available:
            content.entities = self._extract_entities(content.content)
        
        # Analyze sentiment
        if self.config.extract_sentiment and self.local_models_available:
            content.sentiment = self._analyze_sentiment(content.content)
        
        # Detect language
        if self.config.extract_language and self.local_models_available:
            content.language = self._detect_language(content.content)
        
        # Generate summary using AI
        if self.config.summarize_content:
            content.summary = self._generate_summary(content.content)
        
        # Extract tags using AI
        content.tags = self._extract_tags(content.content)
        
        return content
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy"""
        try:
            doc = self.nlp(text[:self.config.max_content_length])
            
            entities = {
                'PERSON': [],
                'ORG': [],
                'GPE': [],  # Geopolitical entities
                'PRODUCT': [],
                'EVENT': [],
                'MONEY': [],
                'DATE': []
            }
            
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
            
            # Remove duplicates
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            return entities
            
        except Exception as e:
            logging.warning(f"⚠️ Entity extraction failed: {e}")
            return {}
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of the text"""
        try:
            # Truncate text if too long
            text = text[:self.config.max_content_length]
            
            result = self.sentiment_pipeline(text)
            
            # Map sentiment labels
            sentiment_map = {
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral',
                'LABEL_2': 'positive'
            }
            
            return sentiment_map.get(result[0]['label'], 'neutral')
            
        except Exception as e:
            logging.warning(f"⚠️ Sentiment analysis failed: {e}")
            return 'neutral'
    
    def _detect_language(self, text: str) -> str:
        """Detect language of the text"""
        try:
            # Simple language detection based on common words
            text_lower = text.lower()
            
            language_indicators = {
                'english': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'],
                'spanish': ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se'],
                'french': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir'],
                'german': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich']
            }
            
            scores = {}
            for lang, words in language_indicators.items():
                score = sum(1 for word in words if word in text_lower)
                scores[lang] = score
            
            return max(scores, key=scores.get) if scores else 'unknown'
            
        except Exception as e:
            logging.warning(f"⚠️ Language detection failed: {e}")
            return 'unknown'
    
    def _generate_summary(self, text: str) -> str:
        """Generate AI-powered summary"""
        try:
            # Use OpenAI if available
            if self.openai_available:
                return self._summarize_with_openai(text)
            
            # Use local model if available
            elif self.local_models_available:
                return self._summarize_with_local(text)
            
            # Fallback to simple extraction
            else:
                return self._simple_summary(text)
                
        except Exception as e:
            logging.warning(f"⚠️ Summary generation failed: {e}")
            return self._simple_summary(text)
    
    def _summarize_with_openai(self, text: str) -> str:
        """Generate summary using OpenAI"""
        try:
            # Truncate text if too long
            text = text[:self.config.max_content_length]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries of web content."},
                    {"role": "user", "content": f"Summarize this content in 2-3 sentences:\n\n{text}"}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.warning(f"⚠️ OpenAI summarization failed: {e}")
            return self._simple_summary(text)
    
    def _summarize_with_local(self, text: str) -> str:
        """Generate summary using local model"""
        try:
            # Split text into chunks if too long
            chunks = self._chunk_text(text, self.config.chunk_size)
            
            summaries = []
            for chunk in chunks:
                summary = self.summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            
            # Combine summaries
            combined_summary = ' '.join(summaries)
            
            # Create final summary
            final_summary = self.summarizer(combined_summary, max_length=150, min_length=50, do_sample=False)
            
            return final_summary[0]['summary_text']
            
        except Exception as e:
            logging.warning(f"⚠️ Local summarization failed: {e}")
            return self._simple_summary(text)
    
    def _simple_summary(self, text: str) -> str:
        """Create simple summary by extracting first few sentences"""
        sentences = re.split(r'[.!?]+', text)
        return '. '.join(sentences[:3]) + '.' if sentences else text[:200] + '...'
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from content"""
        try:
            # Use OpenAI for tag extraction if available
            if self.openai_available:
                return self._extract_tags_with_openai(text)
            
            # Simple keyword extraction as fallback
            else:
                return self._extract_simple_tags(text)
                
        except Exception as e:
            logging.warning(f"⚠️ Tag extraction failed: {e}")
            return []
    
    def _extract_tags_with_openai(self, text: str) -> List[str]:
        """Extract tags using OpenAI"""
        try:
            text = text[:self.config.max_content_length]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts relevant tags from content."},
                    {"role": "user", "content": f"Extract 5-10 relevant tags for this content:\n\n{text}"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip().lower() for tag in tags_text.split(',')]
            return tags[:10]  # Limit to 10 tags
            
        except Exception as e:
            logging.warning(f"⚠️ OpenAI tag extraction failed: {e}")
            return self._extract_simple_tags(text)
    
    def _extract_simple_tags(self, text: str) -> List[str]:
        """Simple tag extraction using keyword frequency"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def _create_empty_content(self, url: str) -> ParsedContent:
        """Create empty content structure for failed parsing"""
        return ParsedContent(
            url=url,
            title="",
            content="",
            summary="",
            extracted_at=datetime.now().isoformat()
        )
    
    def parse_multiple(self, html_contents: Dict[str, str]) -> Dict[str, ParsedContent]:
        """Parse multiple HTML contents"""
        results = {}
        
        for url, html_content in html_contents.items():
            try:
                results[url] = self.parse_html(html_content, url)
            except Exception as e:
                logging.error(f"❌ Failed to parse {url}: {e}")
                results[url] = self._create_empty_content(url)
        
        return results

# Convenience functions
def parse_html_content(html_content: str, url: str = "", config: ParserConfig = None) -> ParsedContent:
    """Quick parse function for HTML content"""
    parser = AIParser(config)
    return parser.parse_html(html_content, url)

def parse_url(url: str, fetcher=None, config: ParserConfig = None) -> ParsedContent:
    """Parse content directly from URL"""
    from .fetcher import StealthFetcher
    
    if not fetcher:
        fetcher = StealthFetcher()
    
    response = fetcher.fetch(url)
    if response and fetcher.validate_response(response):
        parser = AIParser(config)
        return parser.parse_html(response.text, url)
    else:
        return ParsedContent(url=url, title="", content="", summary="")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the parser
    config = ParserConfig(
        use_openai=False,  # Set to True if you have OpenAI API key
        use_local_models=True,
        extract_entities=True,
        extract_sentiment=True,
        summarize_content=True
    )
    
    parser = AIParser(config)
    
    # Test HTML parsing
    test_html = """
    <html>
        <head>
            <title>AI Revolution in Web Scraping</title>
            <meta name="description" content="How AI is transforming web scraping">
        </head>
        <body>
            <h1>AI Revolution in Web Scraping</h1>
            <p>Artificial Intelligence is revolutionizing the way we extract and understand web content. 
            With advanced NLP models and machine learning algorithms, we can now parse complex web pages 
            with unprecedented accuracy and intelligence.</p>
            <p>The future of web scraping lies in AI-powered understanding, not just data extraction.</p>
            <img src="https://example.com/ai-image.jpg" alt="AI Scraping">
            <a href="https://example.com/more-info">Learn More</a>
        </body>
    </html>
    """
    
    result = parser.parse_html(test_html, "https://example.com/article")
    
    print("🧠 Parsing Results:")
    print(f"Title: {result.title}")
    print(f"Summary: {result.summary}")
    print(f"Word Count: {result.word_count}")
    print(f"Reading Time: {result.reading_time} minutes")
    print(f"Sentiment: {result.sentiment}")
    print(f"Language: {result.language}")
    print(f"Tags: {result.tags}")
    print(f"Entities: {result.entities}")
    print(f"Images: {len(result.images)}")
    print(f"Links: {len(result.links)}")
    
    print("\n🧠 AI Parser initialized successfully!")
