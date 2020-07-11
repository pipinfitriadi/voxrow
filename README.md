<!--
Copyright 2020 Pipin Fitriadi <pipinfitriadi@gmail.com>

Licensed under the Microsoft Reference Source License (MS-RSL)

This license governs use of the accompanying software. If you use the
software, you accept this license. If you do not accept the license, do not
use the software.

1. Definitions

The terms "reproduce," "reproduction" and "distribution" have the same
meaning here as under U.S. copyright law.

"You" means the licensee of the software.

"Your company" means the company you worked for when you downloaded the
software.

"Reference use" means use of the software within your company as a reference,
in read only form, for the sole purposes of debugging your products,
maintaining your products, or enhancing the interoperability of your
products with the software, and specifically excludes the right to
distribute the software outside of your company.

"Licensed patents" means any Licensor patent claims which read directly on
the software as distributed by the Licensor under this license.

2. Grant of Rights

(A) Copyright Grant- Subject to the terms of this license, the Licensor
grants you a non-transferable, non-exclusive, worldwide, royalty-free
copyright license to reproduce the software for reference use.

(B) Patent Grant- Subject to the terms of this license, the Licensor grants
you a non-transferable, non-exclusive, worldwide, royalty-free patent
license under licensed patents for reference use.

3. Limitations

(A) No Trademark License- This license does not grant you any rights to use
the Licensor's name, logo, or trademarks.

(B) If you begin patent litigation against the Licensor over patents that
you think may apply to the software (including a cross-claim or counterclaim
in a lawsuit), your license to the software ends automatically.

(C) The software is licensed "as-is." You bear the risk of using it. The
Licensor gives no express warranties, guarantees or conditions. You may have
additional consumer rights under your local laws which this license cannot
change. To the extent permitted under your local laws, the Licensor excludes
the implied warranties of merchantability, fitness for a particular purpose
and non-infringement.
-->

# VOXROW

Daftar isi:

<!-- TOC -->

- [VOXROW](#voxrow)
    - [_Server_](#_server_)
    - [_Source-code_](#_source-code_)
        - [_Editor_](#_editor_)
        - [Repositori Git](#repositori-git)
        - [Tata Cara Penulisan _Markdown_](#tata-cara-penulisan-_markdown_)
        - [Python](#python)
    - [Lisensi](#lisensi)

<!-- /TOC -->

---

## _Server_

Disarankan untuk menggunakan [Ubuntu 18.04 x64](https://ubuntu.com/download/desktop)
(_CPU_ minimal 1 vCore, _RAM_ minimal 512 MB, _Storage_ minimal 10 GB SSD, dan _Bandwidth_
minimal 500 GB), supaya memudahkan pengelolaan _server_ dengan mengunakan _script_
VOXROW. Adapun langkah yang harus dipersiapkan adalah sebagai berikut:

1. Pastikan telah ada _source-code_ VOXROW di komputer lokal dan _server_. Dapat
dipergunakan perintah [Git](https://git-scm.com/) berikut ini:

    ```shell
    $ git clone --recurse-submodules -j8 https://gitlab.com/voxrow/voxrow.git
    ```

    > Jangan jalankan perintah ini di _folder_ `root/` milik _server_!

2. Masuk ke _folder_ `server/`:

    ```shell
    $ cd voxrow/server/
    ```

3. Pastikan [GNU Make](https://www.gnu.org/software/make/) sudah ada, dengan
menjalankan perintah ini:

    ```shell
    $ . install/make_gnu.sh
    ```

    > _Script_ ini hanya dapat dipergunakan di Ubuntu Linux, instalasi untuk OS
    selain ini silahkan cari di internet.

4. Jalankan perintah di komputer lokal dan _server_ sebagai berikut:

    - Komputer lokal:

        Pastikan terlebih dahulu bahwa _SSH Key Pair_ sudah dibuat, baca baik-baik
        instruksi dalam prosesnya! Berikut ini adalah perintahnya:

        ```shell
        $ sudo ssh-keygen
        ```

        Salin _public key_ komputer lokal ke _server_ dengan perintah ini:

        ```shell
        $ make local_ssh_key_to_server
        ```

        Ikuti instruksi yang dimintakan saat proses berjalan.

        > Masukkan alamat _server_ dan _username_ `root`.

    - _Server_:

        > Pastikan anda masuk sebagai _username_ `root`!

        ```shell
        $ make
        ```

        Ikuti instruksi yang dimintakan saat proses berjalan. Setelah proses berakhir
        _server_ akan _reboot_. Selesai _reboot_ masuk kembali dengan _username_
        baru yang telah dibuat.

        [GitLab CI/CD](https://docs.gitlab.com/ee/ci/) dipergunakan untuk mempermudah
        proses _release_ aplikasi. Registrasi [GitLab Runner](https://docs.gitlab.com/runner/)
        di _private server_ perlu dilakukan untuk proses [CI/CD](https://en.wikipedia.org/wiki/CI/CD),
        berikut adalah perintahnya:

        ```shell
        $ make register_runner
        ```

        Setelah seluruh proses selesai dijalankan, maka hapuslah _source-code_
        VOXROW dari _server_, karena sudah tidak diperlukan lagi. Perintahnya
        adalah sebagai berikut:

        ```shell
        $ sudo rm -rf voxrow/
        ```

---

## _Source-code_

> Sebagai catatan beberapa perintah aplikasi di komputer lokal ini dapat berjalan
dengan baik di OS MacOS dan Linux. Adapun untuk OS Windows perlu dilakukan sedikit
penyesuaian.

### _Editor_

[VSCode](https://code.visualstudio.com/) (Visual Studio Code) dipergunakan untuk
memudahkan dalam penulisan _source-code_.

Beberapa _extension_ VSCode dipasangkan untuk memudahkan penulisan _source-code_,
antara lain:

- [_Auto Markdown TOC_](https://marketplace.visualstudio.com/items?itemName=huntertran.auto-markdown-toc)
- [_Markdownlint_](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)
- [_Python extension for Visual Studio Code_](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Jinja](https://marketplace.visualstudio.com/items?itemName=wholroyd.jinja)

### Repositori Git

Git GUI [Sourcetree](https://www.sourcetreeapp.com/) dapat
dipergunakan untuk memudahkan pengelolaan repositori, pada sistem operasi Windows
atau MacOS.

_Branching model_ [Git-Flow](https://github.com/nvie/gitflow) dari Vincent Driessen
dipergunakan untuk memudahkan pengelolaan _feature_, _release_, dan _hotfix_ di
dalam repositori.

### Tata Cara Penulisan _Markdown_

Beberapa sumber ini dapat dijadikan acuan tata cara penulisan _markdown_:

- [_GitLab: List of supported languages and lexers_](https://github.com/rouge-ruby/rouge/wiki/List-of-supported-languages-and-lexers)
- [_GitLab Markdown_](https://docs.gitlab.com/ee/user/markdown.html)
- [_Wikipedia: Markdown_](https://en.m.wikipedia.org/wiki/Markdown)
- [Berkas readme.md yang dibuat oleh Ben Strahan](https://gist.github.com/benstr/8744304#file-readme-md)

### Python

Dipergunakan [Python 3.8.0](https://www.python.org/downloads/release/python-380/)
(versi minimal).

Dalam mengembangkan _source-code_ di komputer lokal, maka pertamakali perlu dibuat
_environtment_ python dengan langkah berikut ini:

1. Pastikan versi python yang dipergunakan sudah sesuai.

    ```shell
    $ python3 -V
    ````

2. Buat _environtment_ python.

    ```shell
    $ python3 -m venv env
    ````

    Instruksi terkait _environtment_ python yang dapat dipergunakan antara lain:

    - Aktivasi:

        ```shell
        $ . env/bin/activate
        ```

        > Kembangkan _source-code_ dengan kondisi _environtment_ python sedang teraktivasi.

    - Deaktivasi:

        ```shell
        (env) $ deactivate
        ```

3. Pastikan [pustaka pendukung](requirements.txt) terpasang di _environtment_ python.

    ```shell
    (env) $ pip install --upgrade pip && pip install -r requirements.txt
    ```

---

## Lisensi

Lisensi yang dipergunakan adalah [MS-RSL](LICENSE) (Microsoft Reference Source License).
