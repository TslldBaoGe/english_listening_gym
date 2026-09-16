<template>
  <el-container style="min-height:100vh">
    <el-header style="padding:0">
      <div class="navbar" style="background:#0a0a0f;border-bottom:1px solid var(--border)">
        <el-menu mode="horizontal" router :default-active="$route.path"
                 style="max-width:1080px;margin:0 auto;border:none">
          <span class="mono" style="font-size:18px;color:var(--accent);align-self:center;
            margin-right:32px;font-weight:700">&lt;EL&gt;</span>
          <el-menu-item index="/practice">练习</el-menu-item>
          <el-menu-item index="/quiz">测验</el-menu-item>
          <el-menu-item index="/stats">统计</el-menu-item>
          <el-menu-item index="/library">知识库</el-menu-item>
          <el-menu-item index="/settings">设置</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main style="padding:0">
      <router-view />
    </el-main>
  </el-container>
</template>
