// AstrBot Plugin API
const API_BASE = '/api/v1/plugin/astrbot_plugin_liflag';

// Default configuration
const DEFAULT_CONFIG = {
    start_word: "我要学习",
    finish_word: "学完了",
    day_word: "今日学习时长",
    week_word: "本周学习时长",
    total_word: "总学习时长",
    guide_words: "打卡说明|学习说明|打卡帮助",
    rename_words: "修改技能|改技能",
    adjust_words: "修改今日时长|改今日时长",
    add_admin_words: "添加管理员",
    remove_admin_words: "删除管理员",
    list_admin_words: "管理员名单",
    min_minutes: 5,
    max_minutes: 180,
    remind_after_minutes: 10,
    keyword_alias: "",
    total_limit: 20,
    start_text: "{name}开始学习{subject}，计划{minutes}分钟",
    start_invalid_text: "请输入学习内容和分钟数",
    start_out_of_range_text: "时长必须在{min}到{max}分钟之间",
    start_already_active_text: "你还有一项学习正在计时，先说学完了再开始新的吧！",
    finish_text: "{name}完成了{subject}，学习了{minutes}分钟",
    finish_too_short_text: "这次不到{min}分钟，将不计入时长，多坚持一下哦！",
    reminder_text: "{name}，{subject}已经学了{overdue}分钟超时啦！",
    hard_stop_text: "已经到{max_minutes}分钟时长上限了哦！快去休息一下吧！",
    day_empty_text: "今天还没学习哦，先来一个？",
    day_header: "今天{name}学习了：",
    day_line: "{subject} {minutes}分钟！",
    total_empty_text: "还没有学习记录哦",
    total_header: "你的总学习时长为：{minutes}分钟，数据如下：",
    total_line: "一共学习了{subject} {minutes}分钟！",
    week_text: "{name}本周学习时长：\n{days}\n\n本周共{minutes}分钟",
    week_day_text: "{month}月{day}日 周{weekday}：{minutes}分钟",
    guide_header: "",
    guide_text: "📚 学习打卡使用说明\n\n▪️ 开始学习：我要学习Python 30分钟\n▪️ 完成学习：学完了\n▪️ 查询今日：今日学习时长\n▪️ 查询本周：本周学习时长\n▪️ 查询总计：总学习时长\n\n💡 提示：\n· 学习时长需在5-180分钟之间\n· 不到5分钟不计入统计\n· 超过180分钟自动结束\n· 所有命令不需要@机器人",
    admin_denied_text: "只有管理员可以使用该命令",
    rename_success_text: "已将{old}映射为{new}",
    adjust_success_text: "已为{subject}添加{minutes}分钟",
    resolve_failed_text: "没有找到唯一匹配的群成员",
    super_admins: "2403232967",
    admin_limit: 20
};

// State
let currentConfig = {};

// DOM elements
const tabs = document.querySelectorAll('.tab-btn');
const panels = document.querySelectorAll('.tab-panel');
const saveBtn = document.getElementById('save');
const resetBtn = document.getElementById('reset');
const toast = document.getElementById('toast');

// Tab switching
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetId = tab.dataset.tab;

        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(targetId).classList.add('active');
    });
});

// Load configuration
async function loadConfig() {
    try {
        const data = await window.AstrBotPluginPage.apiGet('config');
        currentConfig = { ...DEFAULT_CONFIG, ...data };
        populateForm(currentConfig);
        loadAdmins();
    } catch (error) {
        console.error('Load config error:', error);
        showToast('配置加载失败，使用默认值', 'error');
        currentConfig = { ...DEFAULT_CONFIG };
        populateForm(currentConfig);
    }
}

// Load admin list
async function loadAdmins() {
    try {
        const data = await window.AstrBotPluginPage.apiGet('admins');
        renderAdminList(data.admins || []);
    } catch (error) {
        console.error('Load admins error:', error);
        document.getElementById('admin_list').innerHTML = '<p class="hint error">加载失败</p>';
    }
}

// Render admin list
function renderAdminList(admins) {
    const container = document.getElementById('admin_list');
    if (!admins || admins.length === 0) {
        container.innerHTML = '<p class="hint">还没有添加普通管理员</p>';
        return;
    }

    const html = admins.map(admin => {
        const date = new Date(admin.added_at * 1000).toLocaleString('zh-CN');
        return `
            <div class="admin-item">
                <div class="admin-info">
                    <span class="admin-qq">${admin.qq}</span>
                    <span class="admin-date">${date}</span>
                </div>
                <button class="btn btn-danger btn-sm" onclick="removeAdmin('${admin.qq}')">移除</button>
            </div>
        `;
    }).join('');
    container.innerHTML = html;
}

// Add admin
async function addAdmin() {
    const input = document.getElementById('add_admin_qq');
    const qq = input.value.trim();

    if (!qq) {
        showToast('请输入QQ号', 'error');
        return;
    }

    if (!/^\d+$/.test(qq)) {
        showToast('QQ号格式错误', 'error');
        return;
    }

    try {
        await window.AstrBotPluginPage.apiPost('admins/add', { qq });
        showToast('添加成功', 'success');
        input.value = '';
        loadAdmins();
    } catch (error) {
        console.error('Add admin error:', error);
        showToast(error.message || '添加失败', 'error');
    }
}

// Remove admin
async function removeAdmin(qq) {
    if (!confirm(`确定要移除管理员 ${qq} 吗？`)) {
        return;
    }

    try {
        await window.AstrBotPluginPage.apiPost('admins/remove', { qq });
        showToast('移除成功', 'success');
        loadAdmins();
    } catch (error) {
        console.error('Remove admin error:', error);
        showToast(error.message || '移除失败', 'error');
    }
}

// Populate form with config
function populateForm(config) {
    Object.keys(config).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            if (element.type === 'number') {
                element.value = Number(config[key]);
            } else {
                element.value = config[key];
            }
        }
    });
}

// Gather form data
function gatherFormData() {
    const data = {};
    Object.keys(DEFAULT_CONFIG).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            if (element.type === 'number') {
                data[key] = Number(element.value);
            } else {
                data[key] = element.value;
            }
        }
    });
    return data;
}

// Save configuration
async function saveConfig() {
    try {
        const config = gatherFormData();
        await window.AstrBotPluginPage.apiPost('config', config);
        currentConfig = config;
        showToast('配置保存成功', 'success');
    } catch (error) {
        console.error('Save config error:', error);
        showToast('配置保存失败', 'error');
    }
}

// Reset to defaults
function resetConfig() {
    if (confirm('确定要重置为默认配置吗？所有自定义设置将丢失。')) {
        currentConfig = { ...DEFAULT_CONFIG };
        populateForm(currentConfig);
        showToast('已重置为默认配置，点击保存生效', 'success');
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Event listeners
saveBtn.addEventListener('click', saveConfig);
resetBtn.addEventListener('click', resetConfig);
document.getElementById('add_admin_btn').addEventListener('click', addAdmin);

// Make removeAdmin available globally
window.removeAdmin = removeAdmin;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();

    // Detect system theme
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const applyTheme = (e) => {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    };
    applyTheme(darkModeQuery);
    darkModeQuery.addEventListener('change', applyTheme);
});
