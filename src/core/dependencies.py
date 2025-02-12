# async def get_current_user(
#         token: str = Depends(oauth2_scheme)
# ) -> Optional[UserModel]:
#     try:
#         payload = jwt.decode(token,
#                              settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         user_id = payload.get("sub")
#         if user_id is None:
#             raise InvalidTokenException
#     except Exception:
#         raise InvalidTokenException
#     current_user = await UserService.get_user(uuid.UUID(user_id))
#     if not current_user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Verify email")
#     return current_user
#
#
# async def get_current_superuser(current_user: UserModel = Depends(get_current_user)) -> UserModel:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
#     return current_user