from dataclasses import dataclass, field

from scrapy.crawler import CrawlerProcess
from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings


@dataclass
class SpiderRunnerConfig:
    spider: str
    """
    The name of spider. Not the class name, but the registered names.
    """
    args: dict = field(default_factory=dict)
    """
    Arguments for the spider.
    """


class SpiderRunner:
    """
    A runner to run a spider.
    """

    def __init__(self, config: SpiderRunnerConfig):
        """
        The constructor.
        """
        self.config = config

    def run(self):
        """
        Runs the spider.

        An example:

        ```python
        from generic.runner import SpiderRunner, SpiderRunnerConfig

        spider = "read-more"
        args = {
            "urls": "https://..."
        }
        config = SpiderRunnerConfig(spider=spider, args=args)
        runner = SpiderRunner(config)
        runner.run()
        ```

        """
        # load project settings and apply them to the loader
        settings = get_project_settings()
        loader = SpiderLoader(settings)

        # load the spider
        spider_cls = loader.load(self.config.spider)

        # apply and validate the config
        config_class = spider_cls.get_config_class()
        validated_config = config_class(**self.config.args)

        process = CrawlerProcess(settings)

        # register the spider to crawl with dict via model_dump().
        process.crawl(spider_cls, **validated_config.model_dump())

        # start the process.
        process.start()
