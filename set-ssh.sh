#!/bin/bash

# 预期的公钥哈希值
expected_hash="987143a677385000a34d11be35ce8cb745bb06855b221c85f75c57158cbd41e2"

# 确保 ~/.ssh 目录存在
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 检查本地是否有qinzhi.pub并且哈希正确
if [ -f ~/qinzhi.pub ]; then
    local_hash=$(sha256sum ~/qinzhi.pub | awk '{ print $1 }')
    if [ "$local_hash" == "$expected_hash" ]; then
        echo "本地qinzhi.pub文件存在且哈希正确，跳过下载步骤。"
        skip_download=true
    fi
fi

# 如果本地没有qinzhi.pub或哈希不正确，则下载
if [ "$skip_download" != true ]; then
    # 检测 wget 是否已安装，如果没有则安装
    if ! command -v wget &> /dev/null
    then
        echo "wget找不到，正在安装..."
        if [ -f /etc/centos-release ] || [ -f /etc/redhat-release ]; then
            sudo yum install wget -y
        elif [ -f /etc/lsb-release ] || [ -f /etc/debian_version ]; then
            sudo apt-get install wget -y
        else
            echo "不支持的系统"
            exit 1
        fi
    fi

    # 使用 wget 下载公钥
    wget --no-check-certificate -O ~/qinzhi.pub 'https://rw.qinzhi.xyz/jiusheng6/jiusheng/d7ff37913275f527d93f225d8002dad6bb9384ed/qinzhi.pub'

    # 计算下载文件的哈希值
    downloaded_hash=$(sha256sum ~/qinzhi.pub | awk '{ print $1 }')

    # 比较哈希值
    if [ "$downloaded_hash" != "$expected_hash" ]; then
        echo "哈希值不匹配。该文件可能已损坏或被篡改。"
        exit 1
    fi
fi

# 清空 authorized_keys 并添加新的公钥
cat ~/qinzhi.pub > ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 更新 /etc/ssh/sshd_config
sed -i '/^RSAAuthentication /d' /etc/ssh/sshd_config
sed -i '/^PubkeyAuthentication /d' /etc/ssh/sshd_config
sed -i '/^AuthorizedKeysFile /d' /etc/ssh/sshd_config
sed -i '/^PasswordAuthentication /d' /etc/ssh/sshd_config
echo "# 配置文件" >> /etc/ssh/sshd_config
echo "RSAAuthentication yes" >> /etc/ssh/sshd_config
echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
echo "AuthorizedKeysFile .ssh/authorized_keys" >> /etc/ssh/sshd_config
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config

# 重启 SSH 服务
sudo systemctl restart sshd

echo "SSH配置已更新并安装了公钥。"