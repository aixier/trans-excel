<template>
  <div class="knowledge-exam">
    <div class="exam-header">
      <h2>知识考试</h2>
      <div class="exam-status">
        <span>题目 {{ currentQuestionIndex + 1 }} / {{ questions.length }}</span>
      </div>
    </div>

    <div class="exam-container">
      <div class="question-section">
        <div class="question-card">
          <h3>问题</h3>
          <div class="question-content">
            {{ currentQuestion?.question }}
          </div>
          <div class="question-options" v-if="currentQuestion?.options">
            <div
              v-for="(option, index) in currentQuestion.options"
              :key="index"
              class="option-item"
              :class="{ selected: selectedAnswer === option }"
              @click="selectedAnswer = option"
            >
              {{ String.fromCharCode(65 + index) }}. {{ option }}
            </div>
          </div>
        </div>
      </div>

      <div class="answer-section">
        <div class="answer-card">
          <h3>答案</h3>
          <div class="answer-content">
            <div v-if="showAnswer" class="answer-display">
              <div class="correct-answer">
                <strong>正确答案：</strong> {{ currentQuestion?.correctAnswer }}
              </div>
              <div class="explanation" v-if="currentQuestion?.explanation">
                <strong>解释：</strong> {{ currentQuestion?.explanation }}
              </div>
              <div class="answer-result" :class="{ correct: isCorrect, incorrect: !isCorrect }">
                <strong>{{ isCorrect ? '✓ 回答正确' : '✗ 回答错误' }}</strong>
              </div>
            </div>
            <div v-else class="no-answer">
              请先选择答案
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="exam-controls">
      <a-button @click="previousQuestion" :disabled="currentQuestionIndex === 0">
        上一题
      </a-button>

      <a-button
        type="primary"
        @click="checkAnswer"
        :disabled="!selectedAnswer || showAnswer"
      >
        检查答案
      </a-button>

      <a-button
        @click="nextQuestion"
        :disabled="currentQuestionIndex === questions.length - 1"
        v-if="showAnswer"
      >
        下一题
      </a-button>

      <a-button
        type="primary"
        @click="finishExam"
        v-if="currentQuestionIndex === questions.length - 1 && showAnswer"
      >
        完成考试
      </a-button>
    </div>

    <div class="progress-section">
      <a-progress
        :percent="Math.round(((currentQuestionIndex + 1) / questions.length) * 100)"
        size="small"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'

interface Question {
  id: number
  question: string
  options?: string[]
  correctAnswer: string
  explanation?: string
}

const questions = ref<Question[]>([
  {
    id: 1,
    question: "在游戏翻译中，什么是本地化（Localization）？",
    options: [
      "简单的文字翻译",
      "适应目标市场文化和语言习惯的全面改编",
      "只翻译界面文字",
      "改变游戏玩法"
    ],
    correctAnswer: "适应目标市场文化和语言习惯的全面改编",
    explanation: "本地化不仅包括语言翻译，还涉及文化适应、法律合规、技术适配等多个方面。"
  },
  {
    id: 2,
    question: "翻译术语库的主要作用是什么？",
    options: [
      "储存已翻译的内容",
      "确保专业术语翻译的一致性",
      "记录翻译进度",
      "管理翻译团队"
    ],
    correctAnswer: "确保专业术语翻译的一致性",
    explanation: "术语库帮助维护翻译的一致性，特别是在大型项目中确保所有译者使用相同的专业术语翻译。"
  },
  {
    id: 3,
    question: "CAT工具的全称是什么？",
    options: [
      "Computer Assisted Translation",
      "Computer Automatic Translation",
      "Computer Advanced Translation",
      "Computer Aided Translation"
    ],
    correctAnswer: "Computer Assisted Translation",
    explanation: "CAT（Computer Assisted Translation）是计算机辅助翻译工具，帮助译者提高翻译效率和质量。"
  }
])

const currentQuestionIndex = ref(0)
const selectedAnswer = ref('')
const showAnswer = ref(false)
const correctCount = ref(0)

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])

const isCorrect = computed(() => {
  return selectedAnswer.value === currentQuestion.value?.correctAnswer
})

const checkAnswer = () => {
  if (!selectedAnswer.value) {
    message.warning('请先选择一个答案')
    return
  }

  showAnswer.value = true

  if (isCorrect.value) {
    correctCount.value++
    message.success('回答正确！')
  } else {
    message.error('回答错误，请查看正确答案')
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value++
    selectedAnswer.value = ''
    showAnswer.value = false
  }
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    selectedAnswer.value = ''
    showAnswer.value = false
  }
}

const finishExam = () => {
  const score = Math.round((correctCount.value / questions.value.length) * 100)
  message.success(`考试完成！您的得分是：${score}分 (${correctCount.value}/${questions.value.length})`)
}

onMounted(() => {
  // 初始化考试
})
</script>

<style scoped lang="scss">
.knowledge-exam {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  overflow: hidden;

  .exam-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: white;
    border-bottom: 1px solid #e8e8e8;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h2 {
      margin: 0;
      color: #1890ff;
    }

    .exam-status {
      font-size: 14px;
      color: #666;
    }
  }

  .exam-container {
    flex: 1;
    display: flex;
    gap: 16px;
    padding: 16px;
    overflow: hidden;

    .question-section {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .answer-section {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .question-card,
    .answer-card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      height: 100%;
      display: flex;
      flex-direction: column;

      h3 {
        margin: 0;
        padding: 16px 20px;
        border-bottom: 1px solid #e8e8e8;
        background: #f8f9fa;
        border-radius: 8px 8px 0 0;
        color: #333;
        font-size: 16px;
      }

      .question-content,
      .answer-content {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
      }

      .question-content {
        font-size: 16px;
        line-height: 1.6;
        color: #333;
        margin-bottom: 20px;
      }

      .question-options {
        .option-item {
          padding: 12px 16px;
          margin: 8px 0;
          border: 1px solid #d9d9d9;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
          background: #fafafa;

          &:hover {
            border-color: #1890ff;
            background: #e6f7ff;
          }

          &.selected {
            border-color: #1890ff;
            background: #e6f7ff;
            color: #1890ff;
            font-weight: 500;
          }
        }
      }

      .answer-display {
        .correct-answer {
          margin-bottom: 16px;
          padding: 12px;
          background: #f6ffed;
          border: 1px solid #b7eb8f;
          border-radius: 6px;
          color: #52c41a;
        }

        .explanation {
          margin-bottom: 16px;
          padding: 12px;
          background: #e6f7ff;
          border: 1px solid #91d5ff;
          border-radius: 6px;
          color: #1890ff;
          line-height: 1.6;
        }

        .answer-result {
          padding: 12px;
          border-radius: 6px;
          text-align: center;

          &.correct {
            background: #f6ffed;
            border: 1px solid #b7eb8f;
            color: #52c41a;
          }

          &.incorrect {
            background: #fff2f0;
            border: 1px solid #ffccc7;
            color: #ff4d4f;
          }
        }
      }

      .no-answer {
        text-align: center;
        color: #999;
        font-style: italic;
        padding: 40px 20px;
      }
    }
  }

  .exam-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    padding: 16px 24px;
    background: white;
    border-top: 1px solid #e8e8e8;
    box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
  }

  .progress-section {
    padding: 8px 24px;
    background: white;
    border-top: 1px solid #f0f0f0;
  }
}

@media (max-width: 768px) {
  .exam-container {
    flex-direction: column;
    gap: 12px;
    padding: 12px;

    .question-section,
    .answer-section {
      flex: none;
      height: auto;
    }

    .question-card,
    .answer-card {
      min-height: 300px;
    }
  }

  .exam-controls {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>