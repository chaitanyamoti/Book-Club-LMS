(function () {
  function getCsrfToken() {
    var tokenInput = document.querySelector('#logout-form input[name="csrfmiddlewaretoken"]');
    return tokenInput ? tokenInput.value : '';
  }

  function buildAccountMenu() {
    var brandLink = document.getElementById('jazzy-logo');
    if (brandLink) {
      brandLink.setAttribute('href', '/');
      var brandText = brandLink.querySelector('.brand-text');
      if (brandText) {
        brandText.textContent = 'Beyond the Pages';
      }
    }

    var userPanel = document.querySelector('#jazzy-sidebar .user-panel');
    if (userPanel) {
      userPanel.remove();
    }

    var sidebarMenu = document.querySelector('#jazzy-sidebar .nav-sidebar');
    if (!sidebarMenu || document.getElementById('sidebar-account-menu')) {
      return;
    }

    var csrfToken = getCsrfToken();
    var profileLink = document.querySelector('#jazzy-sidebar .user-panel .info a');
    var profileUrl = profileLink ? profileLink.getAttribute('href') : '/admin/auth/user/';
    var accountName = profileLink ? profileLink.textContent.trim() : 'Account';
    var item = document.createElement('li');
    item.className = 'nav-item has-treeview';
    item.id = 'sidebar-account-menu';
    item.innerHTML = [
      '<a href="#" class="nav-link">',
      '<i class="nav-icon fas fa-user-cog"></i>',
      '<p>' + accountName + ' <i class="fas fa-angle-left right"></i></p>',
      '</a>',
      '<ul class="nav nav-treeview">',
      '<li class="nav-item"><a href="/admin/password_change/" class="nav-link"><i class="fas fa-key nav-icon"></i><p>Change password</p></a></li>',
      '<li class="nav-item">',
      '<form method="post" action="/admin/logout/">',
      '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrfToken + '">',
      '<button type="submit" class="nav-link border-0 bg-transparent text-left w-100"><i class="fas fa-sign-out-alt nav-icon"></i><p>Log out</p></button>',
      '</form>',
      '</li>',
      '<li class="nav-item"><a href="/admin/notifications/emaillog/" class="nav-link"><i class="fas fa-mail-bulk nav-icon"></i><p>Email logs</p></a></li>',
      '<li class="nav-item"><a href="/admin/notifications/usernotification/" class="nav-link"><i class="fas fa-bell nav-icon"></i><p>User notifications</p></a></li>',
      '<li class="nav-item"><a href="' + profileUrl + '" class="nav-link"><i class="fas fa-user nav-icon"></i><p>See profile</p></a></li>',
      '</ul>'
    ].join('');

    var dashboardItem = sidebarMenu.querySelector('.nav-item');
    if (dashboardItem) {
      sidebarMenu.insertBefore(item, dashboardItem);
    } else {
      sidebarMenu.appendChild(item);
    }
  }

  document.addEventListener('DOMContentLoaded', buildAccountMenu);
})();
