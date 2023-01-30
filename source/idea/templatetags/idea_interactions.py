


#     if not user.is_anonymous and not idea.idea_archived:
  
#       try:
#           idea.idea_likes[user.username]
#       except KeyError:
#           idea.idea_like_count += 1
#           idea.idea_likes[user.username] = True
#           idea.save()
#       else:
#           idea.idea_like_count -= 1
#           del idea.idea_likes[user.username]
#           idea.save()
#       return True 
#     else:
#       return False