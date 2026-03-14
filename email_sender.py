import asyncio
import sys
import ctypes
import aiodns
import aiosmtplib
from email.message import EmailMessage



# 2. 配置参数
FROM_ADDR = "1@453627.xyz"
TO_ADDR = "3428979959@qq.com"
SUBJECT = "Python 异步直接投递测试"
BODY = "这是通过 Python aiosmtplib 发送的测试邮件。"

async def send_direct_email():
    target_domain = TO_ADDR.split('@')[1]
    print(f"正在异步解析 {target_domain} 的 MX 记录...")

    try:
        # 3. 修复 DNS 解析 (手动指定 nameservers 以解决无法连接问题)
        # 指定 8.8.8.8 (Google) 或 114.114.114.114
        resolver = aiodns.DNSResolver(nameservers=['8.8.8.8', '114.114.114.114'])
        
        # 使用新的 query_dns 方法
        result = await resolver.query_dns(target_domain, 'MX')
        
        # 解析结果结构已变: result.answer 中包含记录
        mx_list = sorted(result.answer, key=lambda x: x.data.priority)
        best_mx = mx_list[0].data.exchange
        print(f"自动获取到 MX 记录: {best_mx} (优先级: {mx_list[0].data.priority})")

        # 构造邮件
        message = EmailMessage()
        message["From"] = FROM_ADDR
        message["To"] = TO_ADDR
        message["Subject"] = SUBJECT
        message.set_content(BODY)

        # 4. 异步投递
        print(f"\n正在尝试连接 {best_mx} 并直接投递邮件...")
        async with aiosmtplib.SMTP(hostname=best_mx, port=25, timeout=10) as smtp:
            await smtp.send_message(message)
            
        print("成功：邮件已提交至目标接收队列！")

    except Exception as e:
        print(f"错误：操作失败。\n具体原因：{e}")

if __name__ == "__main__":
    try:
        asyncio.run(send_direct_email())
    except KeyboardInterrupt:
        pass
    finally:
        input("\n按回车键退出...")
