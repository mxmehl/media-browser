// SPDX-FileCopyrightText: 2025 Max Mehl <https://mehl.mx>
//
// SPDX-License-Identifier: GPL-3.0-only

function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    button.classList.add("secondary");
  });
}
