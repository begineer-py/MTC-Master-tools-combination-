# 一個問題在 AI 模型（GPT-2）中如何得到答案的完整過程

## 0. 前言：模型概覽

GPT-2 為 **Transformer (Decoder-only)** 大型語言模型。核心任務：基於輸入序列預測下一個 token。過程：文本轉數字表示，經多層計算，輸出數字預測，再轉回文本。


## 1. 輸入處理階段 (Input Processing)

### 1.1 Tokenization (分詞)

*   **功能：** 自然語言文本 -> 模型數字序列 (token ID)。

*   **方法：** BPE (Byte Pair Encoding) 分詞器。基於詞彙表與合併規則，文本拆分至子詞單元。

*   **過程：**
    1.  輸入文本：e.g. 「什麼蛋糕最好喫？」
    2.  分詞：`[「, 什, 麼, 蛋, 糕, 最, 好, 喫, ？, 」]`。
    3.  映射：token -> 唯一數字 ID (token ID 序列)。

*   **涉及文件/參數：**
    *   `tokenizer.json`, `vocab.json`, `merges.txt`, `special_tokens_map.json`, `tokenizer_config.json`：定義分詞器轉換。
    *   `vocab_size`: 詞彙表大小 (例如 50257)。


### 1.2 Embedding (嵌入)

*   **功能：** 離散 token ID -> 連續語義向量。模型需向量捕捉語義關係。

*   **組成：** (兩部分相加)
    1.  **Token Embeddings (詞嵌入)：** 各 token ID 對應 `n_embd` 維向量。
    2.  **Positional Embeddings (位置嵌入)：** 為序列中各位置添加位置向量，提供順序信息。`n_positions` 定義最大序列長度。

*   **數學表示：**
    輸入 token ID 序列 $(T = [t_1, t_2, \dots, t_L])$。
    詞嵌入：$E_{token}(t_i)$。
    位置嵌入：$E_{pos}(i)$。
    最終輸入嵌入向量 $X_i$：
    $Input\_Embedding_i = E_{token}(t_i) + E_{pos}(i)$
    所有 token 組成輸入嵌入矩陣 $X \in \mathbb{R}^{L \times n_{embd}}$。

*   **涉及參數：**
    *   `n_embd`: 嵌入向量維度，模型隱藏層總維度 (例如 768)。
    *   `n_positions`: 模型能處理最大序列長度 (例如 1024)。


## 2. 核心處理階段：Transformer 解碼器層 (Transformer Decoder Layers)

GPT-2 模型由 `n_layer` (12) 個解碼器層堆疊。輸入 $X$ 依序經各層轉換。每層含：多頭自注意力機制 + 前饋網路。

**貫穿始終的組件：殘差連接 (Residual Connections) 與 層正規化 (Layer Normalization)**

*   **殘差連接 (Residual Connections)：**
    *   **功能：** 解決深度網路梯度消失，促進信息流。
    *   **數學表示：** 對於任一子層 $Sublayer$，輸入 $X_{input}$，輸出 $X_{output}$ 為：
        $X_{output} = X_{input} + Sublayer(X_{input})$

*   **層正規化 (Layer Normalization)：**
    *   **功能：** 穩定訓練過程，防止內部協變位移。對每個樣本在所有特徵維度上標準化。
    *   **數學表示：** 對於輸入向量 $x$，其層正規化為：
        $LayerNorm(x) = \gamma \odot \frac{x - \mu}{\sigma} + \beta$
        其中 $\mu$ 為 $x$ 的均值，$\sigma$ 為 $x$ 的標準差，$\gamma$ 和 $\beta$ 為可學習的縮放和偏移參數。$\odot$ 表示元素級乘法。
    *   **Pre-LN 結構：** 在每個子層輸入上先應用層正規化，再進行子層計算，最後殘差連接。
        $X_{norm} = LayerNorm(X_{input})$
        $Y_{sublayer} = Sublayer(X_{norm})$
        $X_{output} = X_{input} + Y_{sublayer}$
*   **涉及參數：** `layer_norm_epsilon` (極小常數，防除零)。


### 2.1 多頭自注意力機制 (Multi-Head Self-Attention)

*   **功能：** 動態捕捉序列中 token 間相關性，整合上下文信息。

*   **數學分解：**
    1.  **線性投影 (Linear Projections)：**
        輸入序列表示矩陣 $X \in \mathbb{R}^{L \times n_{embd}}$ ($L$ 為序列長度，$n_{embd}$ 為模型維度) 分別投影到三個低維空間，生成 Query (Q), Key (K), Value (V) 矩陣。通過與三個學習權重矩陣 $W_Q, W_K, W_V$ 相乘實現。
        對每個注意力頭 $i$ ($1 \le i \le n_{head}$)，其權重矩陣為 $W_{Q_i}, W_{K_i}, W_{V_i}$。
        $Q_i = X W_{Q_i}$
        $K_i = X W_{K_i}$
        $V_i = X W_{V_i}$
        其中 $W_{Q_i}, W_{K_i} \in \mathbb{R}^{n_{embd} \times d_k}$，$W_{V_i} \in \mathbb{R}^{n_{embd} \times d_v}$。
        *   $d_k$ (Query/Key 維度)：每個注意力頭處理 Q 和 K 的維度。$d_k = n_{embd} / n_{head}$。
        *   $d_v$ (Value 維度)：每個注意力頭從 V 中提取內容的維度。通常 $d_v = d_k$。
        投影後的 $Q_i, K_i, V_i$ 形狀為 $(L, d_k)$ 或 $(L, d_v)$。

    2.  **單頭注意力計算 $Attention\_Head_i$ (Scaled Dot-Product Attention)：**
        每個注意力頭 $i$ 獨立執行：
        *   **相似度計算：** $Q_i$ 與 $K_i^T$ 矩陣乘法，生成相似度分數矩陣。
            $Scores_i = Q_i K_i^T$
        *   **縮放：** 分數除以 $\sqrt{d_k}$。
            $Scaled\_Scores_i = \frac{Q_i K_i^T}{\sqrt{d_k}}$
        *   **正規化 (Softmax)：** 應用 `softmax` 轉換為注意力權重矩陣。
            $Attention\_Weights_i = softmax(\frac{Q_i K_i^T}{\sqrt{d_k}})$
        *   **加權求和 Value：** 注意力權重矩陣與 $V_i$ 矩陣乘法，整合上下文信息。
            $Output\_SingleHead_i = Attention\_Weights_i V_i$
            **完整的單頭注意力公式：**
            $Attention(Q_i, K_i, V_i) = softmax(\frac{Q_i K_i^T}{\sqrt{d_k}}) V_i$

    3.  **多頭 (Multi-Head)：**
        模型包含 `n_head` (12) 個獨立注意力頭，各頭學習不同注意力模式。
        各頭輸出 $head_i = Output\_SingleHead_i$ (形狀 $(L, d_v)$) 沿維度 $d_v$ 拼接：
        $Concatenated\_Output = Concat(head_1, \dots, head_{n\_head})$
        $Concatenated\_Output$ 形狀為 $(L, n_{embd})$。
        拼接結果經過線性投影 $W_O \in \mathbb{R}^{n_{embd} \times n_{embd}}$，轉換回原始模型維度 $n_{embd}$，作為多頭注意力的最終輸出 $MultiHead\_Output$。
        $MultiHead(X) = Concat(Attention(X W_{Q_1}, X W_{K_1}, X W_{V_1}), \dots, Attention(X W_{Q_{n_{head}}}, X W_{K_{n_{head}}}, X W_{V_{n_{head}}})) W_O$
        其中 $W_{Q_i}, W_{K_i}, W_{V_i}$ 是各頭的線性投影權重矩陣。

*   **計算複雜度 (傳統注意力)：**
    核心瓶頸為 $Q K^T$ 計算，產生 $L \times L$ 矩陣。傳統多頭自注意力的計算複雜度為 **$O(L^2 \cdot n_{embd})$**，簡化為 **$O(L^2)$**。解釋了早期模型受 `n_ctx`（上下文長度）限制的原因。


### 2.2 前饋網路 (Feed-Forward Network, FFN)

*   **功能：** 各 token 獨立非線性轉換與特徵提取。
*   **結構：** 兩線性層 + 激活函數 (`gelu_new`)。
    輸入 $X_{input} \in \mathbb{R}^{L \times n_{embd}}$
    1.  線性層 1：$X_{hidden} = X_{input} W_1 + b_1$，維度從 $n_{embd}$ 擴展到 $n_{inner}$ (通常 $4 \cdot n_{embd}$)。
    2.  激活函數：$X_{activated} = GELU(X_{hidden})$。
    3.  線性層 2：$X_{output} = X_{activated} W_2 + b_2$，維度從 $n_{inner}$ 縮減回 $n_{embd}$。
*   **數學表示：** 對於輸入向量 $x$，FFN 計算如下：
    $FFN(x) = Linear_2(GELU(Linear_1(x))) = GELU(x W_1 + b_1) W_2 + b_2$
    其中 $W_1, b_1, W_2, b_2$ 為可學習的權重和偏置。
*   **涉及參數：**
    *   `activation_function`: 激活函數類型 (例如 `gelu_new`)。
    *   `n_inner`: FFN 內部隱藏層的維度大小。


## 3. 輸出階段 (Output Layer)

*   **功能：** 最終上下文向量 $X_{final}$ -> 下一個 token 概率分佈。
*   **流程：**
    1.  最終 Transformer 層輸出 $X_{final} \in \mathbb{R}^{L \times n_{embd}}$ 送入線性層 (語言模型頭)。
    2.  線性層：$n_{embd}$ 維 -> `vocab_size` 維，輸出 logits 矩陣。
        $Logits = X_{final} \cdot W_{output}$
        $W_{output} \in \mathbb{R}^{n_{embd} \times vocab\_size}$。$Logits$ 形狀 $(L, vocab\_size)$。
    3.  $Logits$ 經 `softmax` -> 概率分佈。
        $Probabilities = softmax(Logits)$
    4.  模型依概率分佈選擇下個 token。
*   **涉及參數：** `vocab_size`。


## 4. 文本生成循環 (Text Generation Loop)

語言模型逐 token 預測生成。

*   **步驟：**
    1.  **初始輸入：** 用戶提示文本。
    2.  **首次預測：**
        *   提示文本分詞嵌入 -> $X_{prompt}$。
        *   $X_{prompt}$ 經 Transformer 解碼器層 -> 輸出層。
        *   輸出層預測下個 token 概率分佈。
        *   **Token 選擇：** 依概率分佈選擇 token。
            *   **貪婪搜索：** 選最高概率 token。
            *   **採樣：** 依概率分佈隨機抽取 token (`"do_sample": true`)。
            *   其他策略：束搜索。
    3.  **構建新輸入：** 新生成 token 加入序列末尾 -> 更長序列 $X_{new\_input}$。
    4.  **迭代預測：** $X_{new\_input}$ 作下次輸入，重複步驟 2、3，直至終止。
*   **終止條件：**
    1.  **生成結束標記 (`"eos_token_id": 50256`)：** 模型預測出結束 token。
    2.  **達到最大長度 (`"max_length": 50`)：** 生成 token 達預設最大限制。
*   **效率優化：KV 緩存 (`"use_cache": true`)**
    生成循環中，模型緩存已計算 Key 和 Value 矩陣。新 token 生成時，僅計算其 K/V，與歷史 K/V 拼接，避免重複計算，加速生成。
