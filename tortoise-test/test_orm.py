"""
This example demonstrates most basic operations with single model
"""
from tortoise import Tortoise, fields, run_async
from tortoise.models import Model


class ResourceDetail(Model):
    id = fields.BigIntField(pk=True, auto_increment=True, description="资源详情ID")
    content = fields.TextField(description="详情内容")
    title = fields.CharField(max_length=255, null=True, description="标题")
    resource_id = fields.IntField(description="资源ID")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    delete_flag = fields.IntField(default=1, description="逻辑删除标识 1: 正常，-1: 删除")

    class Meta:
        table = "resource_detail"
        description = "资源详情表"


async def run():
    await Tortoise.init(db_url="mysql://gpt_app_user:Gpt_App_User123@192.168.10.26:33306/qa_docqa", modules={"models": ["__main__"]})
    write_data = await ResourceDetail.create(content="您的眼睛疼痛有多久了？这种不适感在某个特定的时间段会比较严重吗？例如早上醒来或者晚上？\n", title="名称", resource_id=353607321466748928)
    read_data = await ResourceDetail.filter(id=write_data.id).first()
    write_data2 = await ResourceDetail.create(content="您的眼睛疼痛有多久了？这种不适感在某个特定的时间段会比较严重吗？例如早上醒来或者晚上？\\n", title="名称", resource_id=353607321466748928)
    read_data2 = await ResourceDetail.filter(id=write_data2.id).first()
    import pdb; pdb.set_trace()
    print(read_data.content)
    print(read_data2.content)

if __name__ == "__main__":
    run_async(run())