# UGit 协作指南

> 适用于三手分工制的Git/UGit协作规范

---

## 一、仓库初始化

```bash
# 1. 复制模板到项目目录
cp -r 协同任务模板/ 我的项目/
cd 我的项目/

# 2. 初始化Git
git init
git add .
git commit -m "[初始化] 三手分工协同任务模板"

# 3. 创建分支
git branch dev          # 开发主分支
git branch modeling     # 建模手分支
git branch coding       # 编程手分支
git branch writing      # 论文手分支

# 4. 切换到自己的分支
git checkout modeling   # 建模手用这个
```

---

## 二、分支策略

```
main                    最终交付版本（保护分支）
└── dev                 开发主分支（合并各角色成果）
    ├── modeling        建模手分支
    ├── coding          编程手分支
    └── writing         论文手分支
```

**分支规则**：
- 每个人在自己的分支上工作
- 完成一个阶段后，merge到dev
- dev测试通过后，merge到main
- 不要直接在main上提交

---

## 三、日常工作流

### 开始工作前
```bash
git checkout modeling   # 切换到自己的分支
git pull origin dev     # 拉取最新的dev分支
git merge dev           # 合并到自己的分支
```

### 工作中
```bash
# 正常提交
git add 02_建模手/Q1/xxx.md
git commit -m "[建模手] Q1：完成B*-Tree表示法推导"
```

### 完成一个阶段后
```bash
git push origin modeling

# 发起Merge Request到dev
# 或本地合并：
git checkout dev
git pull origin dev
git merge modeling
git push origin dev
```

---

## 四、提交信息规范

### 格式
```
[角色] 问号：具体做了什么

可选：详细说明（多行）
```

### 角色标签
- `[建模手]` 建模相关
- `[编程手]` 代码相关
- `[论文手]` 论文相关
- `[总控]` 共享文件（任务说明/权威数字表/进度看板）
- `[工具]` 工具脚本/配置

### 好的提交信息
```
[建模手] Q1：完成B*-Tree表示法推导，含解码O(n)证明
[编程手] Q2：修复HPWL计算bug，线长从295k降到220k
[论文手] Q1：正稿v2，补充灵敏度分析章节
[总控] 更新权威数字表，修正死区比例为8.33%
```

### 差的提交信息
```
更新
修改
完成
xxx
```

---

## 五、冲突处理

### 常见冲突场景
1. `00_任务总控/` 下的文件被多人修改
2. `05_辅助文档/` 下的参考资料被多人添加
3. `06_交付物/` 下的最终文件

### 处理原则
1. **先沟通**：发现冲突时，先在群里说一声
2. **权威数字表**：以最新实测数据为准，不要保留旧值
3. **任务说明/进度看板**：合并双方的修改
4. **论文正稿**：以论文手的版本为准，其他人的建议写在评论里

### 解决冲突
```bash
git pull origin dev
# 打开冲突文件，找到 <<<<<<< 标记
# 手动解决后：
git add 冲突文件
git commit -m "[总控] 解决冲突：合并xxx"
```

---

## 六、大文件管理

### 什么是大文件
- 图片 > 1MB
- 数据文件 > 10MB
- 论文PDF > 5MB

### 使用Git LFS
```bash
# 安装Git LFS（一次）
git lfs install

# 跟踪大文件类型
git lfs track "*.png"
git lfs track "*.pdf"
git lfs track "*.zip"

# 正常提交即可
git add .gitattributes
git add 图片.png
git commit -m "[论文手] 添加Q1主图"
```

### 不建议入库的文件
- 临时生成的实验数据（放在本地，用完删）
- 编译产物（__pycache__、.pyc）
- 编辑器配置（.vscode、.idea）

用 `.gitignore` 排除：
```
__pycache__/
*.pyc
*.pyo
.vscode/
.idea/
*.tmp
*.log
```

---

## 七、协作纪律

### 必须做
1. ✅ 每天至少pull一次，避免冲突累积
2. ✅ 只在自己的目录下提交
3. ✅ 提交信息写清楚做了什么
4. ✅ 大文件用Git LFS
5. ✅ 完成阶段后及时merge到dev
6. ✅ 修改共享文件前先沟通

### 禁止做
1. ❌ 直接在main分支上提交
2. ❌ 改别人目录下的文件（有建议写反馈）
3. ❌ 强制推送（git push --force）
4. ❌ 提交大文件不用LFS
5. ❌ 提交信息写"更新""修改"
6. ❌ 删除别人的文件（要删先沟通）

---

## 八、常用命令速查

```bash
# 查看状态
git status

# 查看修改
git diff

# 查看历史
git log --oneline --graph

# 撤销修改（未提交）
git checkout -- 文件名

# 撤销提交（保留修改）
git reset --soft HEAD~1

# 暂存当前修改
git stash
git stash pop

# 查看分支
git branch -a

# 切换分支
git checkout 分支名

# 合并分支
git merge 分支名
```

---

## 九、一句话

> **Git不是备份工具，是协作工具。好的提交信息和分支策略，比多提交几次重要得多。**
