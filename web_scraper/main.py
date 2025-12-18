"""
🧠 WEB SCRAPER ORCHESTRATOR — The Master Brain 🎯
Main orchestration system that coordinates all web scraping operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import re
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal
import sys

# Import our modules
from .core.fetcher import StealthFetcher, ScrapingConfig
from .core.parser import AIParser, ParserConfig, ParsedContent
from .core.browser import DynamicBrowser, BrowserConfig
from .utils.storage import DataStorage, StorageConfig
from .utils.logger import WebScrapingLogger, LogConfig

@dataclass
class ScrapingJob:
    """Individual scraping job definition"""
    url: str
    job_id: str
    priority: int = 1  # 1-10, higher is more important
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    use_browser: bool = False
    wait_for_selector: str = None
    scroll_to_bottom: bool = False
    extract_images: bool = True
    extract_links: bool = True
    custom_headers: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    scheduled_for: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ScrapingSession:
    """Scraping session configuration"""
    session_id: str
    name: str
    urls: List[str]
    config: Dict[str, Any] = None
    filters: Dict[str, Any] = None
    post_processors: List[Callable] = None
    created_at: datetime = None
    status: str = "pending"  # pending, running, completed, failed, paused
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.config is None:
            self.config = {}
        if self.filters is None:
            self.filters = {}
        if self.post_processors is None:
            self.post_processors = []

@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    max_concurrent_jobs: int = 10
    max_concurrent_browsers: int = 3
    job_queue_size: int = 1000
    retry_delay: int = 5
    session_timeout: int = 3600  # 1 hour
    auto_save_interval: int = 300  # 5 minutes
    enable_scheduling: bool = True
    enable_monitoring: bool = True
    enable_metrics: bool = True
    shutdown_timeout: int = 30
    log_level: str = "INFO"

class WebScrapingOrchestrator:
    """
    🧠 Master orchestrator for web scraping operations
    """
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
        
        # Initialize components
        self.logger = WebScrapingLogger(LogConfig(log_level=self.config.log_level))
        self.storage = DataStorage(StorageConfig())
        
        # Job management
        self.job_queue = queue.PriorityQueue(maxsize=self.config.job_queue_size)
        self.active_jobs: Dict[str, ScrapingJob] = {}
        self.completed_jobs: Dict[str, ScrapingJob] = {}
        self.failed_jobs: Dict[str, ScrapingJob] = {}
        
        # Session management
        self.active_sessions: Dict[str, ScrapingSession] = {}
        self.session_results: Dict[str, List[ParsedContent]] = {}
        
        # Threading and async
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_jobs)
        self.browser_pool = []
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Metrics
        self.metrics = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_bytes': 0,
            'total_pages': 0,
            'start_time': None,
            'last_activity': None
        }
        
        # Initialize fetcher and parser
        self.fetcher = StealthFetcher(ScrapingConfig())
        self.parser = AIParser(ParserConfig())
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.log_info("Web Scraping Orchestrator initialized")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.log_info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the orchestrator"""
        if self.running:
            self.logger.log_warning("Orchestrator is already running")
            return
        
        self.running = True
        self.metrics['start_time'] = datetime.now()
        
        # Start worker threads
        self._start_worker_threads()
        
        # Start monitoring thread
        if self.config.enable_monitoring:
            self._start_monitoring_thread()
        
        # Start auto-save thread
        self._start_autosave_thread()
        
        self.logger.log_info("Orchestrator started successfully")
    
    def shutdown(self):
        """Shutdown the orchestrator gracefully"""
        if not self.running:
            return
        
        self.logger.log_info("Initiating orchestrator shutdown...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for active jobs to complete
        timeout = self.config.shutdown_timeout
        start_time = time.time()
        
        while self.active_jobs and (time.time() - start_time) < timeout:
            self.logger.log_info(f"Waiting for {len(self.active_jobs)} active jobs to complete...")
            time.sleep(1)
        
        # Force shutdown remaining jobs
        if self.active_jobs:
            self.logger.log_warning(f"Force shutting down {len(self.active_jobs)} remaining jobs")
            for job_id in list(self.active_jobs.keys()):
                self._cancel_job(job_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close browsers
        for browser in self.browser_pool:
            try:
                asyncio.run(browser.close())
            except:
                pass
        
        # Save final metrics
        self._save_metrics()
        
        self.logger.log_info("Orchestrator shutdown complete")
    
    def _start_worker_threads(self):
        """Start worker threads for job processing"""
        for i in range(self.config.max_concurrent_jobs):
            worker = threading.Thread(
                target=self._worker_thread,
                name=f"Worker-{i}",
                daemon=True
            )
            worker.start()
    
    def _start_monitoring_thread(self):
        """Start monitoring thread for metrics and health checks"""
        def monitor():
            while self.running and not self.shutdown_event.is_set():
                try:
                    self._update_metrics()
                    self._health_check()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.log_error("Error in monitoring thread", e)
        
        monitor_thread = threading.Thread(target=monitor, name="Monitor", daemon=True)
        monitor_thread.start()
    
    def _start_autosave_thread(self):
        """Start auto-save thread for periodic data saving"""
        def autosave():
            while self.running and not self.shutdown_event.is_set():
                try:
                    time.sleep(self.config.auto_save_interval)
                    self._auto_save()
                except Exception as e:
                    self.logger.log_error("Error in autosave thread", e)
        
        autosave_thread = threading.Thread(target=autosave, name="AutoSave", daemon=True)
        autosave_thread.start()
    
    def _worker_thread(self):
        """Worker thread for processing jobs"""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get job from queue (with timeout)
                try:
                    priority, job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process job
                self._process_job(job)
                
            except Exception as e:
                self.logger.log_error("Error in worker thread", e)
    
    def _process_job(self, job: ScrapingJob):
        """Process a single scraping job"""
        job_id = job.job_id
        
        try:
            # Move to active jobs
            self.active_jobs[job_id] = job
            
            # Log job start
            self.logger.log_info(f"Processing job: {job_id}", 
                               url=job.url, priority=job.priority)
            
            # Process based on job requirements
            if job.use_browser:
                result = self._process_with_browser(job)
            else:
                result = self._process_with_fetcher(job)
            
            if result:
                # Parse content
                parsed_content = self.parser.parse_html(result, job.url)
                
                # Apply post-processors
                for processor in job.metadata.get('post_processors', []):
                    parsed_content = processor(parsed_content)
                
                # Store result
                self._store_result(job_id, parsed_content)
                
                # Move to completed
                self.completed_jobs[job_id] = job
                self.metrics['completed_jobs'] += 1
                
                self.logger.log_info(f"Completed job: {job_id}")
                
            else:
                # Handle failure
                self._handle_job_failure(job)
        
        except Exception as e:
            self.logger.log_error(f"Error processing job {job_id}", e)
            self._handle_job_failure(job)
        
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job_id, None)
    
    def _process_with_fetcher(self, job: ScrapingJob) -> Optional[str]:
        """Process job using stealth fetcher"""
        try:
            # Configure fetcher for this job
            fetcher_config = ScrapingConfig(
                timeout=job.timeout,
                max_retries=job.max_retries
            )
            
            if job.custom_headers:
                # Apply custom headers
                pass  # Implementation would go here
            
            # Fetch content
            response = self.fetcher.fetch(job.url)
            
            if response and self.fetcher.validate_response(response):
                return response.text
            
            return None
            
        except Exception as e:
            self.logger.log_error(f"Fetcher error for job {job.job_id}", e)
            return None
    
    def _process_with_browser(self, job: ScrapingJob) -> Optional[str]:
        """Process job using browser automation"""
        try:
            # Get or create browser
            browser = self._get_browser()
            
            # Configure browser
            browser_config = BrowserConfig(
                timeout=job.timeout,
                wait_for_selector=job.wait_for_selector,
                scroll_to_bottom=job.scroll_to_bottom
            )
            
            # Process with browser
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self._browser_process(browser, job, browser_config)
                )
                return result
            finally:
                loop.close()
            
        except Exception as e:
            self.logger.log_error(f"Browser error for job {job.job_id}", e)
            return None
    
    async def _browser_process(self, browser: DynamicBrowser, job: ScrapingJob, config: BrowserConfig) -> Optional[str]:
        """Async browser processing"""
        try:
            success = await browser.navigate(job.url)
            if success:
                if config.scroll_to_bottom:
                    await browser.scroll_to_bottom()
                
                if config.wait_for_selector:
                    await browser.wait_for_element(config.wait_for_selector)
                
                return await browser.get_content()
            
            return None
            
        except Exception as e:
            self.logger.log_error(f"Async browser error for job {job.job_id}", e)
            return None
    
    def _get_browser(self) -> DynamicBrowser:
        """Get or create browser instance"""
        # Simple implementation - in production, implement proper pooling
        return DynamicBrowser(BrowserConfig())
    
    def _handle_job_failure(self, job: ScrapingJob):
        """Handle job failure with retry logic"""
        job.retry_count += 1
        
        if job.retry_count < job.max_retries:
            # Retry job
            self.logger.log_warning(f"Retrying job {job.job_id} (attempt {job.retry_count + 1})")
            
            # Add delay before retry
            time.sleep(self.config.retry_delay)
            
            # Re-queue job
            self.job_queue.put((job.priority, job))
        else:
            # Max retries reached
            self.failed_jobs[job.job_id] = job
            self.metrics['failed_jobs'] += 1
            
            self.logger.log_error(f"Job {job.job_id} failed after {job.max_retries} retries")
    
    def _store_result(self, job_id: str, content: ParsedContent):
        """Store scraping result"""
        try:
            # Store in database
            self.storage.save_sqlite(content)
            
            # Update metrics
            self.metrics['total_bytes'] += len(content.content)
            self.metrics['total_pages'] += 1
            self.metrics['last_activity'] = datetime.now()
            
        except Exception as e:
            self.logger.log_error(f"Error storing result for job {job_id}", e)
    
    def _cancel_job(self, job_id: str):
        """Cancel a job"""
        if job_id in self.active_jobs:
            job = self.active_jobs.pop(job_id)
            self.failed_jobs[job_id] = job
            self.logger.log_info(f"Cancelled job: {job_id}")
    
    def _update_metrics(self):
        """Update system metrics"""
        self.metrics['total_jobs'] = len(self.completed_jobs) + len(self.failed_jobs)
        
        # Calculate uptime
        if self.metrics['start_time']:
            uptime = datetime.now() - self.metrics['start_time']
            self.metrics['uptime_seconds'] = uptime.total_seconds()
    
    def _health_check(self):
        """Perform health check"""
        try:
            # Check queue size
            queue_size = self.job_queue.qsize()
            if queue_size > self.config.job_queue_size * 0.8:
                self.logger.log_warning(f"Job queue is {queue_size}% full")
            
            # Check active jobs
            if len(self.active_jobs) > self.config.max_concurrent_jobs * 0.9:
                self.logger.log_warning(f"High number of active jobs: {len(self.active_jobs)}")
            
            # Check memory usage (simplified)
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 80:
                self.logger.log_warning(f"High memory usage: {memory_percent}%")
            
        except Exception as e:
            self.logger.log_error("Error in health check", e)
    
    def _auto_save(self):
        """Auto-save system state"""
        try:
            # Save metrics
            self._save_metrics()
            
            # Save session states
            self._save_session_states()
            
            self.logger.log_info("Auto-save completed")
            
        except Exception as e:
            self.logger.log_error("Error in auto-save", e)
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            metrics_file = Path("scraping_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            self.logger.log_error("Error saving metrics", e)
    
    def _save_session_states(self):
        """Save session states"""
        try:
            sessions_file = Path("active_sessions.json")
            sessions_data = {
                session_id: {
                    'name': session.name,
                    'status': session.status,
                    'created_at': session.created_at.isoformat(),
                    'urls_count': len(session.urls)
                }
                for session_id, session in self.active_sessions.items()
            }
            
            with open(sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
        except Exception as e:
            self.logger.log_error("Error saving session states", e)
    
    # Public API methods
    
    def add_job(self, url: str, job_id: str = None, priority: int = 1, **kwargs) -> str:
        """Add a single job to the queue"""
        if not job_id:
            job_id = f"job_{int(time.time())}_{hash(url) % 10000}"
        
        job = ScrapingJob(
            url=url,
            job_id=job_id,
            priority=priority,
            **kwargs
        )
        
        try:
            self.job_queue.put((priority, job), block=False)
            self.logger.log_info(f"Added job: {job_id}", url=url, priority=priority)
            return job_id
        except queue.Full:
            self.logger.log_error(f"Job queue is full, cannot add job: {job_id}")
            return ""
    
    def add_jobs(self, urls: List[str], priority: int = 1, **kwargs) -> List[str]:
        """Add multiple jobs to the queue"""
        job_ids = []
        
        for url in urls:
            job_id = self.add_job(url, priority=priority, **kwargs)
            if job_id:
                job_ids.append(job_id)
        
        return job_ids
    
    def create_session(self, name: str, urls: List[str], **config) -> str:
        """Create a scraping session"""
        session_id = f"session_{int(time.time())}_{hash(name) % 10000}"
        
        session = ScrapingSession(
            session_id=session_id,
            name=name,
            urls=urls,
            config=config
        )
        
        self.active_sessions[session_id] = session
        self.session_results[session_id] = []
        
        self.logger.log_info(f"Created session: {session_id}", name=name, urls_count=len(urls))
        
        return session_id
    
    def start_session(self, session_id: str):
        """Start a scraping session"""
        if session_id not in self.active_sessions:
            self.logger.log_error(f"Session not found: {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        session.status = "running"
        
        # Add jobs for all URLs
        job_ids = self.add_jobs(session.urls, metadata={'session_id': session_id})
        
        self.logger.log_info(f"Started session: {session_id}", jobs_count=len(job_ids))
        return True
    
    def pause_session(self, session_id: str):
        """Pause a scraping session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "paused"
            self.logger.log_info(f"Paused session: {session_id}")
    
    def resume_session(self, session_id: str):
        """Resume a paused session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "running"
            self.logger.log_info(f"Resumed session: {session_id}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                'status': 'active',
                'url': job.url,
                'priority': job.priority,
                'retry_count': job.retry_count,
                'created_at': job.created_at.isoformat()
            }
        elif job_id in self.completed_jobs:
            return {'status': 'completed'}
        elif job_id in self.failed_jobs:
            return {'status': 'failed'}
        else:
            return {'status': 'not_found'}
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status"""
        if session_id not in self.active_sessions:
            return {'status': 'not_found'}
        
        session = self.active_sessions[session_id]
        return {
            'status': session.status,
            'name': session.name,
            'urls_count': len(session.urls),
            'created_at': session.created_at.isoformat(),
            'results_count': len(self.session_results.get(session_id, []))
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self.metrics.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'metrics': self.metrics,
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'failed_jobs': len(self.failed_jobs),
            'queue_size': self.job_queue.qsize(),
            'active_sessions': len(self.active_sessions),
            'uptime': self.metrics.get('uptime_seconds', 0),
            'logger_stats': self.logger.get_operation_stats(),
            'storage_stats': self.storage.get_stats()
        }

# Convenience functions
def create_orchestrator(config: OrchestratorConfig = None) -> WebScrapingOrchestrator:
    """Create and return orchestrator instance"""
    return WebScrapingOrchestrator(config)

def quick_scrape(urls: List[str], use_browser: bool = False) -> List[ParsedContent]:
    """Quick scraping function for simple use cases"""
    orchestrator = WebScrapingOrchestrator()
    orchestrator.start()
    
    try:
        # Add jobs
        job_ids = orchestrator.add_jobs(urls, use_browser=use_browser)
        
        # Wait for completion
        while orchestrator.active_jobs:
            time.sleep(1)
        
        # Get results from storage
        results = []
        for job_id in job_ids:
            if job_id in orchestrator.completed_jobs:
                # Get result from storage
                search_results = orchestrator.storage.search_content("")
                results.extend(search_results)
        
        return results
        
    finally:
        orchestrator.shutdown()

# Example usage
if __name__ == "__main__":
    # Test orchestrator
    config = OrchestratorConfig(
        max_concurrent_jobs=5,
        log_level="DEBUG"
    )
    
    orchestrator = WebScrapingOrchestrator(config)
    
    try:
        # Start orchestrator
        orchestrator.start()
        
        # Add some test jobs
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml"
        ]
        
        job_ids = orchestrator.add_jobs(test_urls)
        print(f"Added {len(job_ids)} jobs")
        
        # Create a session
        session_id = orchestrator.create_session("Test Session", test_urls)
        orchestrator.start_session(session_id)
        
        # Monitor progress
        for i in range(30):  # Wait up to 30 seconds
            stats = orchestrator.get_stats()
            print(f"Active jobs: {stats['active_jobs']}, Completed: {stats['completed_jobs']}")
            
            if stats['active_jobs'] == 0:
                break
            
            time.sleep(1)
        
        # Print final stats
        final_stats = orchestrator.get_stats()
        print(f"\nFinal Stats: {json.dumps(final_stats, indent=2, default=str)}")
        
    finally:
        orchestrator.shutdown()
    
    print("\n🧠 Web Scraping Orchestrator test completed!")
