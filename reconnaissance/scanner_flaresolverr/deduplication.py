import logging
from instance.models import db, crawler_each_html
from sqlalchemy import func
import sys


def setup_logging():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handler.stream.reconfigure(encoding='utf-8')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

class HTMLDeduplicator:
    def __init__(self, crawler_id=None):
        self.crawler_id = crawler_id

    def deduplicate(self):
        """執行去重操作"""
        try:
            logger.info("開始執行 HTML 記錄去重...")
            
            # 查詢所有重複的 URL
            duplicates = db.session.query(
                crawler_each_html.html_url,
                func.count(crawler_each_html.id).label('count'),
                func.min(crawler_each_html.id).label('keep_id')
            ).group_by(
                crawler_each_html.html_url
            ).having(
                func.count(crawler_each_html.id) > 1
            )


            if self.crawler_id:
                duplicates = duplicates.filter(crawler_each_html)

            duplicates = duplicates.all()
            
            if not duplicates:
                logger.info("未發現重複的 URL")
                return True

            logger.info(f"發現 {len(duplicates)} 個重複的 URL")
            
            # 開始處理重複記錄
            total_deleted = 0
            for url, count, keep_id in duplicates:
                try:
                    # 刪除重複記錄，保留最早的一條
                    deleted = db.session.query(crawler_each_html).filter(
                        crawler_each_html.html_url == url,
                        crawler_each_html.id != keep_id
                    )
                    

                    if self.crawler_id:
                        deleted = deleted.filter(crawler_each_html.crawler_id == self.crawler_id)
                    

                    deleted_count = deleted.delete(synchronize_session=False)
                    total_deleted += deleted_count
                    
                    logger.info(f"URL '{url}' - 保留ID {keep_id}, 刪除了 {deleted_count} 條重複記錄")
                    
                except Exception as e:
                    logger.error(f"處理 URL '{url}' 時出錯: {str(e)}")
                    continue

            # 提交更改
            try:
                db.session.commit()
                logger.info(f"去重完成，共刪除 {total_deleted} 條重複記錄")
                return True
            except Exception as e:
                logger.error(f"提交更改時出錯: {str(e)}")
                db.session.rollback()
                return False
                
        except Exception as e:
            logger.error(f"去重過程出錯: {str(e)}")
            db.session.rollback()
            return False

def main(crawler_id=None):
    """主函數"""
    try:
        deduplicator = HTMLDeduplicator(crawler_id)
        success = deduplicator.deduplicate()
        return success
    except Exception as e:
        logger.error(f"執行去重時出錯: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='HTML 記錄去重工具')
    parser.add_argument('--crawler-id', type=int, help='指定 crawler ID 進行去重')
    args = parser.parse_args()
    
    success = main(args.crawler_id)
    sys.exit(0 if success else 1) 