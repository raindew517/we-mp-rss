
import core.wx as wx 
import core.db as db
from core.config import DEBUG,cfg
from core.models.article import Article


def delete_article(id:str):
    try:
        DB=db.Db(tag="文章API")
        session=DB.get_session()
        article = session.query(Article).filter(Article.id == id).first()
        session.delete(article)
        session.commit()
    except Exception as e:
        print(e)
        pass



def UpdateArticle(art:dict):
    mps_count=0
    if DEBUG:
        delete_article(art['id'])
        pass
    DB=db.Db(tag="文章API")
    if  DB.add_article(art):
        mps_count=mps_count+1
        return True
    return False
def Update_Over(data=None):
    print("更新完成",data)
    pass